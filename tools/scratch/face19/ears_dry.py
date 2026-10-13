import sys
sys.path.insert(0, "tools/assets")
import heroine_ears as he
from PIL import Image
Image.Image.save = lambda *a, **k: None
he.main(sys.argv[1:])
