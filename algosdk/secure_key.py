from password_strength import PasswordPolicy, PasswordStats
from algosdk import mnemonic, logic, account
from Crypto.Cipher import AES

import random
import json
import base64
import getpass
import hashlib


class InvalidPasswordError(Exception):
    def __init__(self):
        self.message = "Invalid password!"


class SecureKey:
    def __init__(self, filename):
        self.filename = filename

    def write_key(self, pk=None, passwword=None, description=None):
        print("Please copy and paste your private key mnemonic below")
        while mnem is None:
            mnem = getpass.getpass("Mnemonic: ")
            mnem = mnem.replace(",", " ").replace("  ", " ")
            try:
                pk = mnemonic.to_private_key(mnem)
                print("Key address: " + account.address_from_private_key(pk))
            except:
                if len(mnem.split(" ") != 25):
                    print("Mnemonic must be 25 words long. Please retry.")
                else:
                    print("Invalid mnemonic. Please retry.")
                mnem = None

        address = account.address_from_private_key(pk)
        nonce1 = str(random.random())
        nonce2 = str(random.random())

        while password is None:
            password1 = getpass.getpass("Choose a password: ")
            password2 = getpass.getpass("Confirm password: ")
            strength = PasswordStats(password1).strength()
            if password1 != password2:
                print("Passwords don't match, please retry.")
            elif len(password1) < 12:
                print("Password is not long enough, please retry.")
            elif strength < 0.66:
                print("Password complexity score is " + str(strength) + ".")
                print("Must be at least 0.66. Please retry.")
            else:
                password = password1
                print("Password strength score: " + str(strength))

        if description is None:
            description = input("Key description: ")
        encrypt_key = hashlib.sha256(
            (nonce1 + password).encode("utf-8")
        ).digest()
        init_vector = hashlib.sha256(nonce2.encode("utf-8")).digest()[:16]
        encryption_suite = AES.new(encrypt_key, AES.MODE_CBC, init_vector)

        padded_input = mnem + ((16 - len(mnem) % 16) % 16) * " "
        padded_input = padded_input.encode("utf-8")
        encrypted_data = encryption_suite.encrypt(padded_input)
        encrypted_b64 = base64.b64encode(encrypted_data).decode("utf-8")

        file_data = {
            "nonce1": nonce1,
            "nonce2": nonce2,
            "address": address,
            "encrypt_key": encrypted_b64,
            "description": description,
        }
        open(self.filename, "w").write(json.dumps(file_data))

    def load_key(self, password=None):
        data = json.loads(open(self.filename).read())
        nonce1 = data["nonce1"]
        nonce2 = data["nonce2"]

        encrypted_b64 = base64.b64decode(data["encrypt_key"].encode("utf-8"))
        if password is None:
            print("Decrypting key: " + self.filename)
            print("Key address: " + data["address"])
            print("Descripton: " + data["description"])

        while True:
            if password:
                password1 = password
            else:
                password1 = getpass.getpass("Enter password: ")

            key = hashlib.sha256((nonce1 + password1).encode("utf-8")).digest()
            init_vector = hashlib.sha256(nonce2.encode("utf-8")).digest()[:16]
            encryption_suite = AES.new(key, AES.MODE_CBC, init_vector)
            try:
                decrypted = encryption_suite.decrypt(encrypted_b64).decode(
                    "utf-8"
                )
            except:
                if password:
                    raise InvalidPasswordError()
                else:
                    print("Invalid password. Please try again.")
                    continue
            break
        pk = mnemonic.to_private_key(decrypted)
        return pk


def main():
    enc_key = SecureKey("my_key.json")
    enc_key.write_key()
    print(" ")
    loaded_key = SecureKey("my_key.json").load_key()


if __name__ == "__main__":
    main()
