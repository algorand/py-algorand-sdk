from . import constants
from . import encoding
import decimal
import base64
from algosdk.future import ApplicationCallTxn, OnComplete
from nacl.signing import SigningKey, VerifyKey
from nacl.exceptions import BadSignatureError


def microalgos_to_algos(microalgos):
    """
    Convert microalgos to algos.

    Args:
        microalgos (int): how many microalgos

    Returns:
        int or decimal: how many algos
    """
    return decimal.Decimal(microalgos) / constants.microalgos_to_algos_ratio


def algos_to_microalgos(algos):
    """
    Convert algos to microalgos.

    Args:
        algos (int or decimal): how many algos

    Returns:
        int: how many microalgos
    """
    return round(algos * constants.microalgos_to_algos_ratio)


def sign_bytes(to_sign, private_key):
    """
    Sign arbitrary bytes after prepending with "MX" for domain separation.

    Args:
        to_sign (bytes): bytes to sign

    Returns:
        str: base64 signature
    """
    to_sign = constants.bytes_prefix + to_sign
    private_key = base64.b64decode(private_key)
    signing_key = SigningKey(private_key[:constants.key_len_bytes])
    signed = signing_key.sign(to_sign)
    signature = base64.b64encode(signed.signature).decode()
    return signature


def verify_bytes(message, signature, public_key):
    """
    Verify the signature of a message that was prepended with "MX" for domain
    separation.

    Args:
        message (bytes): message that was signed, without prefix
        signature (str): base64 signature
        public_key (str): base32 address

    Returns:
        bool: whether or not the signature is valid
    """
    verify_key = VerifyKey(encoding.decode_address(public_key))
    prefixed_message = constants.bytes_prefix + message
    try:
        verify_key.verify(prefixed_message, base64.b64decode(signature))
        return True
    except BadSignatureError:
        return False


def make_unsigned_app_create_transaction(sender, sp, on_complete, approval_program, clear_program, global_schema,
                                         local_schema,
                                         app_args=None, accounts=None, foreign_apps=None, note=None, lease=None,
                                         rekey_to=None):
    """
    Make a transaction that will create an application.

    Args:
        sender (str): address of sender
        sp (SuggestedParams): contains information such as fee and genesis hash
        on_complete (OnComplete): what application should so once the program is done being run
        approval_program (bytes): the compiled TEAL that approves a transaction
        clear_program (bytes): the compiled TEAL that runs when clearing state
        global_schema (StateSchema): restricts the number of ints and byte slices in the global state
        local_schema (StateSchema): restructs the number of ints and byte slices in the per-user local state
        app_args(list[bytes], optional): any additional arguments to the application
        accounts(list[str], optional): any additional accounts to supply to the application
        foreign_apps(list[int], optional): any other apps used by the application, identified by app index
        note(bytes, optional): transaction note field
        lease(bytes, optional): transaction lease field
        rekey_to(str, optional): rekey-to field, see Transaction
    """
    return future.ApplicationCallTxn(sender=sender, sp=sp, index=0, on_complete=on_complete,
                                     approval_program=approval_program, clear_program=clear_program,
                                     global_schema=global_schema,
                                     local_schema=local_schema, app_args=app_args, accounts=accounts,
                                     foreign_apps=foreign_apps, note=note, lease=lease, rekey_to=rekey_to)


def make_unsigned_app_update_transaction(sender, sp, index, approval_program, clear_program, app_args=None,
                                         accounts=None, foreign_apps=None,
                                         note=None, lease=None, rekey_to=None):
     """
     Make a transaction that will change an application's approval and clear programs.

     Args:
         sender (str): address of sender
         sp (SuggestedParams): contains information such as fee and genesis hash
         index (int): the application to update
         approval_program (bytes): the new compiled TEAL that approves a transaction
         clear_program (bytes): the new compiled TEAL that runs when clearing state
         app_args(list[bytes], optional): any additional arguments to the application
         accounts(list[str], optional): any additional accounts to supply to the application
         foreign_apps(list[int], optional): any other apps used by the application, identified by app index
         note(bytes, optional): transaction note field
         lease(bytes, optional): transaction lease field
         rekey_to(str, optional): rekey-to field, see Transaction
     """
     return future.ApplicationCallTxn(sender=sender, sp=sp, index=index, on_complete=OnComplete.UpdateApplicationOC,
                                     approval_program=approval_program, clear_program=clear_program,
                                     app_args=app_args, accounts=accounts, foreign_apps=foreign_apps, note=note,
                                     lease=lease, rekey_to=rekey_to)


def make_unsigned_app_delete_tx(sender, sp, index, app_args=None, accounts=None, foreign_apps=None,
                                note=None, lease=None, rekey_to=None):
    """
    Make a transaction that will delete an application

    Args:
        sender (str): address of sender
        sp (SuggestedParams): contains information such as fee and genesis hash
        index (int): the application to update
        app_args(list[bytes], optional): any additional arguments to the application
        accounts(list[str], optional): any additional accounts to supply to the application
        foreign_apps(list[int], optional): any other apps used by the application, identified by app index
        note(bytes, optional): transaction note field
        lease(bytes, optional): transaction lease field
        rekey_to(str, optional): rekey-to field, see Transaction
    """
    return future.ApplicationCallTxn(sender=sender, sp=sp, index=index, on_complete=OnComplete.DeleteApplicationOC,
                                     app_args=app_args, accounts=accounts, foreign_apps=foreign_apps, note=note,
                                     lease=lease, rekey_to=rekey_to)


def make_unsigned_app_opt_in_tx(sender, sp, index, app_args=None, accounts=None, foreign_apps=None,
                                note=None, lease=None, rekey_to=None):
    """
    Make a transaction that will opt in to an application

    Args:
        sender (str): address of sender
        sp (SuggestedParams): contains information such as fee and genesis hash
        index (int): the application to update
        app_args(list[bytes], optional): any additional arguments to the application
        accounts(list[str], optional): any additional accounts to supply to the application
        foreign_apps(list[int], optional): any other apps used by the application, identified by app index
        note(bytes, optional): transaction note field
        lease(bytes, optional): transaction lease field
        rekey_to(str, optional): rekey-to field, see Transaction
    """
    return future.ApplicationCallTxn(sender=sender, sp=sp, index=index, on_complete=OnComplete.OptInOC,
                                     app_args=app_args, accounts=accounts, foreign_apps=foreign_apps, note=note,
                                     lease=lease, rekey_to=rekey_to)


def make_unsigned_app_close_out_tx(sender, sp, index, app_args=None, accounts=None, foreign_apps=None,
                                   note=None, lease=None, rekey_to=None):
    """
    Make a transaction that will close out a user's state in an application

    Args:
        sender (str): address of sender
        sp (SuggestedParams): contains information such as fee and genesis hash
        index (int): the application to update
        app_args(list[bytes], optional): any additional arguments to the application
        accounts(list[str], optional): any additional accounts to supply to the application
        foreign_apps(list[int], optional): any other apps used by the application, identified by app index
        note(bytes, optional): transaction note field
        lease(bytes, optional): transaction lease field
        rekey_to(str, optional): rekey-to field, see Transaction
    """
    return future.ApplicationCallTxn(sender=sender, sp=sp, index=index, on_complete=OnComplete.CloseOutOC,
                                     app_args=app_args, accounts=accounts, foreign_apps=foreign_apps, note=note,
                                     lease=lease, rekey_to=rekey_to)


def make_unsigned_app_clear_state_tx(sender, sp, index, app_args=None, accounts=None, foreign_apps=None,
                                     note=None, lease=None, rekey_to=None):
    """
    Make a transaction that will clear a user's state an application

    Args:
        sender (str): address of sender
        sp (SuggestedParams): contains information such as fee and genesis hash
        index (int): the application to update
        app_args(list[bytes], optional): any additional arguments to the application
        accounts(list[str], optional): any additional accounts to supply to the application
        foreign_apps(list[int], optional): any other apps used by the application, identified by app index
        note(bytes, optional): transaction note field
        lease(bytes, optional): transaction lease field
        rekey_to(str, optional): rekey-to field, see Transaction
    """
    return future.ApplicationCallTxn(sender=sender, sp=sp, index=index, on_complete=OnComplete.ClearStateOC,
                                     app_args=app_args, accounts=accounts, foreign_apps=foreign_apps, note=note,
                                     lease=lease, rekey_to=rekey_to)


def make_unsigned_app_no_op_tx(sender, sp, index, app_args=None, accounts=None, foreign_apps=None,
                               note=None, lease=None, rekey_to=None):
    """
    Make a transaction that will do nothing on application completion
     In other words, just call the application

    Args:
        sender (str): address of sender
        sp (SuggestedParams): contains information such as fee and genesis hash
        index (int): the application to update
        app_args(list[bytes], optional): any additional arguments to the application
        accounts(list[str], optional): any additional accounts to supply to the application
        foreign_apps(list[int], optional): any other apps used by the application, identified by app index
        note(bytes, optional): transaction note field
        lease(bytes, optional): transaction lease field
        rekey_to(str, optional): rekey-to field, see Transaction
    """
    return future.ApplicationCallTxn(sender=sender, sp=sp, index=index, on_complete=OnComplete.NoOpOC,
                                     app_args=app_args, accounts=accounts, foreign_apps=foreign_apps, note=note,
                                     lease=lease, rekey_to=rekey_to)