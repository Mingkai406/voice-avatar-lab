"""Create local-only expression inputs from an upstream sample or your own crop."""
import argparse,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--image',type=Path,help='A consented, front-facing square face crop');args=p.parse_args()
from PIL import Image
if args.image:im=Image.open(args.image).convert('RGB').resize((256,256))
else:
    import cv2
    capture=cv2.VideoCapture(str(ROOT/'vendor/DH_live/web_demo/static/assets/01.mp4'))
    ok,frame=capture.read();capture.release()
    if not ok:raise SystemExit('Missing upstream sample video. Run setup first.')
    full=Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB));w,h=full.size
    # Fixed crop for the pinned sample, not a general face detector.
    im=full.crop((int(.15*w),int(.09*h),int(.85*w),int(.09*h+.7*w))).resize((256,256))
im.save(ROOT/'public/source-crop.jpg')
# These are source-image placeholders, not claims of completed neural inference.
for name in ['lp-neutral.jpg','lp-smile.jpg']:im.save(ROOT/'public'/name)
print('Expression source prepared locally. Generate in Expression Lab to run inference.')
