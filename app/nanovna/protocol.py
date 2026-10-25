"""Firmware adapters keep command syntax isolated and observable."""
import re, struct
class ProtocolError(RuntimeError): pass
class NanoVNAProtocol:
    prompt=b"ch>"
    def info_commands(self): return [b"info\r",b"version\r"]
    def sweep_command(self,start,stop,points): return f"sweep {start} {stop} {points}\r".encode()
    def data_command(self,channel): return f"data {channel}\r".encode()
    def parse_complex(self,raw,expected):
        values=[]
        for line in raw.decode(errors="replace").splitlines():
            nums=re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?",line)
            if len(nums)>=2:
                try: values.append(complex(float(nums[-2]),float(nums[-1])))
                except ValueError: pass
        if len(values)!=expected: raise ProtocolError(f"Expected {expected} values, received {len(values)}")
        return values

class NanoVNAV2Protocol:
    """NanoRFE V2 register/FIFO wire protocol."""
    NOP=0x00; INDICATE=0x0D; READ=0x10; READ_FIFO=0x18
    WRITE=0x20; WRITE2=0x21; WRITE8=0x23
    SWEEP_START=0x00; SWEEP_STEP=0x10; SWEEP_POINTS=0x20
    VALUES_PER_FREQUENCY=0x22; VALUES_FIFO=0x30
    DEVICE_VARIANT=0xF0; PROTOCOL_VERSION=0xF1; HARDWARE_REVISION=0xF2
    FIRMWARE_MAJOR=0xF3; FIRMWARE_MINOR=0xF4
    RECORD_SIZE=32

    @staticmethod
    def reset_command(): return bytes(8)
    @classmethod
    def read_register(cls,address): return bytes((cls.READ,address))
    @classmethod
    def configure_sweep(cls,start,stop,points):
        if points < 2: raise ProtocolError("A V2 sweep requires at least two points")
        step=round((stop-start)/(points-1))
        return (struct.pack("<BBQ",cls.WRITE8,cls.SWEEP_START,int(start))+
                struct.pack("<BBQ",cls.WRITE8,cls.SWEEP_STEP,int(step))+
                struct.pack("<BBH",cls.WRITE2,cls.SWEEP_POINTS,points)+
                struct.pack("<BBH",cls.WRITE2,cls.VALUES_PER_FREQUENCY,1))
    @classmethod
    def clear_fifo(cls): return bytes((cls.WRITE,cls.VALUES_FIFO,0))
    @classmethod
    def read_fifo(cls,count):
        if not 1 <= count <= 255: raise ProtocolError("V2 FIFO request must contain 1-255 records")
        return bytes((cls.READ_FIFO,cls.VALUES_FIFO,count))
    @classmethod
    def parse_fifo(cls,payload,points):
        expected=points*cls.RECORD_SIZE
        if len(payload)!=expected: raise ProtocolError(f"Expected {expected} FIFO bytes, received {len(payload)}")
        s11=[None]*points; s21=[None]*points
        for offset in range(0,len(payload),cls.RECORD_SIZE):
            fwd_re,fwd_im,refl_re,refl_im,thru_re,thru_im,index=struct.unpack_from("<iiiiiihxxxxxx",payload,offset)
            if not 0 <= index < points: raise ProtocolError(f"V2 FIFO frequency index {index} is outside 0-{points-1}")
            fwd=complex(fwd_re,fwd_im)
            if abs(fwd)==0: raise ProtocolError(f"V2 FIFO returned a zero forward signal at index {index}")
            if s11[index] is not None: raise ProtocolError(f"V2 FIFO returned duplicate frequency index {index}")
            s11[index]=complex(refl_re,refl_im)/fwd; s21[index]=complex(thru_re,thru_im)/fwd
        missing=[i for i,value in enumerate(s11) if value is None]
        if missing: raise ProtocolError(f"V2 FIFO is missing {len(missing)} frequency indices")
        return s11,s21
