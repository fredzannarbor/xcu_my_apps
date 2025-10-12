import bcrypt

# Generate a new hash for a known password
new_password = "hotdogtoy"
salt = bcrypt.gensalt()
new_hash = bcrypt.hashpw(new_password.encode('utf-8'), salt)
print(new_hash.decode('utf-8'))
