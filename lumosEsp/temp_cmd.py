# If os is not imported, import it
try:
    import os
except ImportError:
    pass

# List the files in the current directory
print(os.listdir())

# Delete the file
os.remove("boot.py")
os.remove("main.py")
os.remove("./static/index.html")

# Create a new folder
os.mkdir("static")
os.mkdir("static/css")
os.mkdir("static/js")

# Move the file to the new folder
os.rename("index.html", "static/index.html")
os.rename("index.min.html", "static/index.html")
os.rename("pico.indigo.min.css", "static/css/pico.indigo.min.css")

# cd to the new folder
os.chdir("css")

# Check how many storage is available
print(os.statvfs("/"))

import micropython
micropython.mem_info()

wlan.disconnect()

# Rename touch_test.py to main.py
os.rename("touch_test.py", "main.py")