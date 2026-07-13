# Deadbolt
## By Null

Deadbolt is a simple app that lets you lock down your files with "high-grade" encryption.
You simply just choose the file in the app or drag and drag to lock or unlock them.

## How it Works

When you drag a file in and set a password, Deadbolt scrambles it using AES-256 encryption.
It also adds a special safety tag (HMAC) to the file. This means if anyone tries to mess with the file's data while it's locked, the app will know and refuse to open it.

Once locked, your file is saved in a brand new format: `.ppfbn`
To get your file back, you just drop that `.ppfbn` file back into the app, type your password, and click unlock. 

## WARNING

### Deadbolt is completely private and local.
### It does not save your passwords anywhere.
Heck, there isn't even a copy password button

### If you forget the password you used to lock a file, there is no "forgot password" button and no way to crack it. 
**Make sure you don't forget your password!**
