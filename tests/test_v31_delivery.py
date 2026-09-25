from pathlib import Path
import numpy as np, soundfile as sf
from castwise_audio_doctor.delivery_engine import deliver

def test_delivery_engine(tmp_path):
    sr=48000
    t=np.arange(sr*2)/sr
    y=(0.15*np.sin(2*np.pi*440*t)).astype('float32')
    src=tmp_path/'source.wav'; sf.write(src,y,sr,subtype='PCM_24')
    m=deliver(src,tmp_path/'out','Radio')
    assert m['version']=='3.1.0'
    assert Path(m['delivery']['path']).exists()
    assert Path(tmp_path/'out'/'source_CASTWISE_delivery.json').exists()
    assert m['delivery']['sha256']
