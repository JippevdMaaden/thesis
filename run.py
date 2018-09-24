import sys
import os

# run flask application

os.system('tmux new -s speckly_webserver')
os.system('python flask/speckly_app.py')
sys.exit(0)

print 'im still working'
