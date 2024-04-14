# If os is not imported, import it
try:
    import os
except ImportError:
    pass

# List the files in the current directory
print(os.listdir())

# Delete the file
os.remove("main.py")
os.remove("./static/index.html")
os.remove("bootstrap.js")

# Create a new folder
os.mkdir("static/js")

# Move the file to the new folder
os.rename("index.html", "static/index.html")

# cd to the new folder
os.chdir("..")

# Check how many storage is available
print(os.statvfs("/"))
