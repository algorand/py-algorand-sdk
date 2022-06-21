import random
import string
import unittest

from algosdk import account, encoding, error
from algosdk.abi import (
    ABIType,
    AddressType,
    ArrayDynamicType,
    ArrayStaticType,
    BoolType,
    ByteType,
    Contract,
    Interface,
    Method,
    NetworkInfo,
    StringType,
    TupleType,
    UfixedType,
    UintType,
)


class TestABIType(unittest.TestCase):
    def test_make_type_valid(self):
        # Test for uint
        for uint_index in range(8, 513, 8):
            uint_type = UintType(uint_index)
            self.assertEqual(str(uint_type), f"uint{uint_index}")
            actual = ABIType.from_string(str(uint_type))
            self.assertEqual(uint_type, actual)

        # Test for ufixed
        for size_index in range(8, 513, 8):
            for precision_index in range(1, 161):
                ufixed_type = UfixedType(size_index, precision_index)
                self.assertEqual(
                    str(ufixed_type), f"ufixed{size_index}x{precision_index}"
                )
                actual = ABIType.from_string(str(ufixed_type))
                self.assertEqual(ufixed_type, actual)

        test_cases = [
            # Test for byte/bool/address/strings
            (ByteType(), f"byte"),
            (BoolType(), f"bool"),
            (AddressType(), f"address"),
            (StringType(), f"string"),
            # Test for dynamic array type
            (
                ArrayDynamicType(UintType(32)),
                f"uint32[]",
            ),
            (
                ArrayDynamicType(ArrayDynamicType(ByteType())),
                f"byte[][]",
            ),
            (
                ArrayDynamicType(UfixedType(256, 64)),
                f"ufixed256x64[]",
            ),
            # Test for static array type
            (
                ArrayStaticType(UfixedType(128, 10), 100),
                f"ufixed128x10[100]",
            ),
            (
                ArrayStaticType(
                    ArrayStaticType(BoolType(), 256),
                    100,
                ),
                f"bool[256][100]",
            ),
            # Test for tuple
            (TupleType([]), f"()"),
            (
                TupleType(
                    [
                        UintType(16),
                        TupleType(
                            [
                                ByteType(),
                                ArrayStaticType(AddressType(), 10),
                            ]
                        ),
                    ]
                ),
                f"(uint16,(byte,address[10]))",
            ),
            (
                TupleType(
                    [
                        UintType(256),
                        TupleType(
                            [
                                ByteType(),
                                ArrayStaticType(AddressType(), 10),
                            ]
                        ),
                        TupleType([]),
                        BoolType(),
                    ]
                ),
                f"(uint256,(byte,address[10]),(),bool)",
            ),
            (
                TupleType(
                    [
                        UfixedType(256, 16),
                        TupleType(
                            [
                                TupleType(
                                    [
                                        StringType(),
                                    ]
                                ),
                                BoolType(),
                                TupleType(
                                    [
                                        AddressType(),
                                        UintType(8),
                                    ]
                                ),
                            ]
                        ),
                    ]
                ),
                f"(ufixed256x16,((string),bool,(address,uint8)))",
            ),
        ]
        for test_case in test_cases:
            self.assertEqual(str(test_case[0]), test_case[1])
            self.assertEqual(test_case[0], ABIType.from_string(test_case[1]))

    def test_make_type_invalid(self):
        # Test for invalid uint
        invalid_type_sizes = [-1, 0, 9, 513, 1024]
        for i in invalid_type_sizes:
            with self.assertRaises(error.ABITypeError) as e:
                UintType(i)
            self.assertIn(f"unsupported uint bitSize: {i}", str(e.exception))
        with self.assertRaises(TypeError) as e:
            UintType()

        # Test for invalid ufixed
        invalid_precisions = [-1, 0, 161]
        for i in invalid_type_sizes:
            with self.assertRaises(error.ABITypeError) as e:
                UfixedType(i, 1)
            self.assertIn(f"unsupported ufixed bitSize: {i}", str(e.exception))
        for j in invalid_precisions:
            with self.assertRaises(error.ABITypeError) as e:
                UfixedType(8, j)
            self.assertIn(
                f"unsupported ufixed precision: {j}", str(e.exception)
            )

    def test_type_from_string_invalid(self):
        test_cases = (
            # uint
            "uint 8",
            "uint8 ",
            "uint123x345",
            "uint!8",
            "uint[32]",
            "uint-893",
            "uint#120\\",
            # ufixed
            "ufixed000000000016x0000010",
            "ufixed123x345",
            "ufixed 128 x 100",
            "ufixed64x10 ",
            "ufixed!8x2 ",
            "ufixed[32]x16",
            "ufixed-64x+100",
            "ufixed16x+12",
            # dynamic array
            "byte[] ",
            "[][][]",
            "stuff[]",
            # static array
            "ufixed32x10[0]",
            "byte[10 ]",
            "uint64[0x21]",
            # tuple
            "(ufixed128x10))",
            "(,uint128,byte[])",
            "(address,ufixed64x5,)",
            "(byte[16],somethingwrong)",
            "(                )",
            "((uint32)",
            "(byte,,byte)",
            "((byte),,(byte))",
        )
        for test_case in test_cases:
            with self.assertRaises(error.ABITypeError) as e:
                ABIType.from_string(test_case)

    def test_is_dynamic(self):
        test_cases = [
            (UintType(32), False),
            (UfixedType(16, 10), False),
            (ByteType(), False),
            (BoolType(), False),
            (AddressType(), False),
            (StringType(), True),
            (
                ArrayDynamicType(ArrayDynamicType(ByteType())),
                True,
            ),
            # Test tuple child types
            (ABIType.from_string("(string[100])"), True),
            (ABIType.from_string("(address,bool,uint256)"), False),
            (ABIType.from_string("(uint8,(byte[10]))"), False),
            (ABIType.from_string("(string,uint256)"), True),
            (
                ABIType.from_string("(bool,(ufixed16x10[],(byte,address)))"),
                True,
            ),
            (
                ABIType.from_string("(bool,(uint256,(byte,address,string)))"),
                True,
            ),
        ]
        for test_case in test_cases:
            self.assertEqual(test_case[0].is_dynamic(), test_case[1])

    def test_byte_len(self):
        test_cases = [
            (AddressType(), 32),
            (ByteType(), 1),
            (BoolType(), 1),
            (UintType(64), 8),
            (UfixedType(256, 50), 32),
            (ABIType.from_string("bool[81]"), 11),
            (ABIType.from_string("bool[80]"), 10),
            (ABIType.from_string("bool[88]"), 11),
            (ABIType.from_string("address[5]"), 160),
            (ABIType.from_string("uint16[20]"), 40),
            (ABIType.from_string("ufixed64x20[10]"), 80),
            (ABIType.from_string(f"(address,byte,ufixed16x20)"), 35),
            (
                ABIType.from_string(
                    f"((bool,address[10]),(bool,bool,bool),uint8[20])"
                ),
                342,
            ),
            (ABIType.from_string(f"(bool,bool)"), 1),
            (ABIType.from_string(f"({'bool,'*6}uint8)"), 2),
            (
                ABIType.from_string(f"({'bool,'*10}uint8,{'bool,'*10}byte)"),
                6,
            ),
        ]
        for test_case in test_cases:
            self.assertEqual(test_case[0].byte_len(), test_case[1])

    def test_byte_len_invalid(self):
        test_cases = (
            StringType(),
            ArrayDynamicType(UfixedType(16, 64)),
        )

        for test_case in test_cases:
            with self.assertRaises(error.ABITypeError) as e:
                test_case.byte_len()


class TestABIEncoding(unittest.TestCase):
    def test_uint_encoding(self):
        uint_test_values = [0, 1, 10, 100, 254]
        for uint_size in range(8, 513, 8):
            for val in uint_test_values:
                uint_type = UintType(uint_size)
                actual = uint_type.encode(val)
                self.assertEqual(len(actual), uint_type.bit_size // 8)
                expected = val.to_bytes(uint_size // 8, byteorder="big")
                self.assertEqual(actual, expected)

                # Test decoding
                actual = uint_type.decode(actual)
                expected = val
                self.assertEqual(actual, expected)
            # Test for the upper limit of each bit size
            val = 2**uint_size - 1
            uint_type = UintType(uint_size)
            actual = uint_type.encode(val)
            self.assertEqual(len(actual), uint_type.bit_size // 8)

            expected = val.to_bytes(uint_size // 8, byteorder="big")
            self.assertEqual(actual, expected)

            actual = uint_type.decode(actual)
            expected = val
            self.assertEqual(actual, expected)

            # Test bad values
            with self.assertRaises(error.ABIEncodingError) as e:
                UintType(uint_size).encode(-1)
            with self.assertRaises(error.ABIEncodingError) as e:
                UintType(uint_size).encode(2**uint_size)
            with self.assertRaises(error.ABIEncodingError) as e:
                UintType(uint_size).decode("ZZZZ")
            with self.assertRaises(error.ABIEncodingError) as e:
                UintType(uint_size).decode(b"\xFF" * (uint_size // 8 + 1))

    def test_ufixed_encoding(self):
        ufixed_test_values = [0, 1, 10, 100, 254]
        for ufixed_size in range(8, 513, 8):
            for precision in range(1, 161):
                for val in ufixed_test_values:
                    ufixed_type = UfixedType(ufixed_size, precision)
                    actual = ufixed_type.encode(val)
                    self.assertEqual(len(actual), ufixed_type.bit_size // 8)

                    expected = val.to_bytes(ufixed_size // 8, byteorder="big")
                    self.assertEqual(actual, expected)

                    # Test decoding
                    actual = ufixed_type.decode(actual)
                    expected = val
                    self.assertEqual(actual, expected)
            # Test for the upper limit of each bit size
            val = 2**ufixed_size - 1
            ufixed_type = UfixedType(ufixed_size, precision)
            actual = ufixed_type.encode(val)
            self.assertEqual(len(actual), ufixed_type.bit_size // 8)

            expected = val.to_bytes(ufixed_size // 8, byteorder="big")
            self.assertEqual(actual, expected)

            actual = ufixed_type.decode(actual)
            expected = val
            self.assertEqual(actual, expected)

            # Test bad values
            with self.assertRaises(error.ABIEncodingError) as e:
                UfixedType(ufixed_size, 10).encode(-1)
            with self.assertRaises(error.ABIEncodingError) as e:
                UfixedType(ufixed_size, 10).encode(2**ufixed_size)
            with self.assertRaises(error.ABIEncodingError) as e:
                UfixedType(ufixed_size, 10).decode("ZZZZ")
            with self.assertRaises(error.ABIEncodingError) as e:
                UfixedType(ufixed_size, 10).decode(
                    b"\xFF" * (ufixed_size // 8 + 1)
                )

    def test_bool_encoding(self):
        actual = BoolType().encode(True)
        expected = bytes.fromhex("80")
        self.assertEqual(actual, expected)
        actual = BoolType().decode(actual)
        expected = True
        self.assertEqual(actual, expected)

        actual = BoolType().encode(False)
        expected = bytes.fromhex("00")
        self.assertEqual(actual, expected)
        actual = BoolType().decode(actual)
        expected = False
        self.assertEqual(actual, expected)

        with self.assertRaises(error.ABIEncodingError) as e:
            ByteType().encode("1")
        with self.assertRaises(error.ABIEncodingError) as e:
            BoolType().decode(bytes.fromhex("8000"))
        with self.assertRaises(error.ABIEncodingError) as e:
            BoolType().decode(bytes.fromhex("30"))

    def test_byte_encoding(self):
        for i in range(255):
            # Pass in an int type to encode
            actual = ByteType().encode(i)
            expected = bytes([i])
            self.assertEqual(actual, expected)

            # Test decoding
            actual = ByteType().decode(actual)
            expected = i
            self.assertEqual(actual, expected)

        # Try to encode a bad byte
        with self.assertRaises(error.ABIEncodingError) as e:
            ByteType().encode(256)
        with self.assertRaises(error.ABIEncodingError) as e:
            ByteType().encode(-1)
        with self.assertRaises(error.ABIEncodingError) as e:
            ByteType().encode((256).to_bytes(2, byteorder="big"))
        with self.assertRaises(error.ABIEncodingError) as e:
            ByteType().decode(bytes.fromhex("8000"))
        with self.assertRaises(error.ABIEncodingError) as e:
            ByteType().decode((256).to_bytes(2, byteorder="big"))

    def test_address_encoding(self):
        for _ in range(100):
            # Generate 100 random addresses as strings and as 32-byte public keys
            random_addr_str = account.generate_account()[1]
            addr_type = AddressType()
            actual = addr_type.encode(random_addr_str)
            expected = encoding.decode_address(random_addr_str)
            self.assertEqual(actual, expected)

            actual = addr_type.encode(expected)
            self.assertEqual(actual, expected)

            # Test decoding
            actual = addr_type.decode(actual)
            expected = random_addr_str
            self.assertEqual(actual, expected)

    def test_string_encoding(self):
        # Test *some* valid combinations of UTF-8 characters
        chars = string.ascii_letters + string.digits + string.punctuation
        for _ in range(1000):
            test_case = "".join(
                random.choice(chars) for i in range(random.randint(0, 1000))
            )
            str_type = StringType()
            str_len = len(test_case).to_bytes(2, byteorder="big")
            expected = str_len + bytes(test_case, "utf-8")
            actual = str_type.encode(test_case)
            self.assertEqual(actual, expected)

            # Test decoding
            actual = str_type.decode(actual)
            self.assertEqual(actual, test_case)

        with self.assertRaises(error.ABIEncodingError) as e:
            StringType().decode((0).to_bytes(1, byteorder="big"))
        with self.assertRaises(error.ABIEncodingError) as e:
            StringType().decode((1).to_bytes(2, byteorder="big"))

    def test_array_static_encoding(self):
        test_cases = [
            (
                ArrayStaticType(BoolType(), 3),
                [True, True, False],
                bytes([0b11000000]),
            ),
            (
                ArrayStaticType(BoolType(), 2),
                [False, True],
                bytes([0b01000000]),
            ),
            (
                ArrayStaticType(BoolType(), 8),
                [False, True, False, False, False, False, False, False],
                bytes([0b01000000]),
            ),
            (
                ArrayStaticType(BoolType(), 8),
                [True, True, True, True, True, True, True, True],
                bytes([0b11111111]),
            ),
            (
                ArrayStaticType(BoolType(), 9),
                [True, False, False, True, False, False, True, False, True],
                bytes.fromhex("92 80"),
            ),
            (
                ArrayStaticType(UintType(64), 3),
                [1, 2, 3],
                bytes.fromhex(
                    "00 00 00 00 00 00 00 01 00 00 00 00 00 00 00 02 00 00 00 00 00 00 00 03"
                ),
            ),
            (
                ArrayStaticType(ByteType(), 17),
                [0, 0, 0, 0, 0, 0, 4, 3, 31, 0, 0, 0, 0, 0, 0, 0, 33],
                bytes.fromhex(
                    "00 00 00 00 00 00 04 03 1f 00 00 00 00 00 00 00 21"
                ),
            ),
        ]

        for test_case in test_cases:
            actual = test_case[0].encode(test_case[1])
            expected = test_case[2]
            self.assertEqual(actual, expected)

            # Test decoding
            actual = test_case[0].decode(actual)
            expected = test_case[1]
            self.assertEqual(actual, expected)

        # Test if bytes can be passed into array
        actual_bytes = b"\x05\x04\x03\x02\x01\x00"
        actual = ArrayStaticType(ByteType(), 6).encode(actual_bytes)
        expected = bytes([5, 4, 3, 2, 1, 0])
        # self.assertEqual sometimes has problems with byte comparisons
        assert actual == expected

        actual = ArrayStaticType(ByteType(), 6).decode(expected)
        expected = [5, 4, 3, 2, 1, 0]
        assert actual == expected

        with self.assertRaises(error.ABIEncodingError) as e:
            ArrayStaticType(BoolType(), 3).encode([True, False])

        with self.assertRaises(error.ABIEncodingError) as e:
            ArrayStaticType(AddressType(), 2).encode([True, False])

    def test_array_dynamic_encoding(self):
        test_cases = [
            (
                ArrayDynamicType(BoolType()),
                [],
                bytes.fromhex("00 00"),
            ),
            (
                ArrayDynamicType(BoolType()),
                [True, True, False],
                bytes.fromhex("00 03 C0"),
            ),
            (
                ArrayDynamicType(BoolType()),
                [False, True, False, False, False, False, False, False],
                bytes.fromhex("00 08 40"),
            ),
            (
                ArrayDynamicType(BoolType()),
                [True, False, False, True, False, False, True, False, True],
                bytes.fromhex("00 09 92 80"),
            ),
        ]

        for test_case in test_cases:
            actual = test_case[0].encode(test_case[1])
            expected = test_case[2]
            self.assertEqual(actual, expected)

            # Test decoding
            actual = test_case[0].decode(actual)
            expected = test_case[1]
            self.assertEqual(actual, expected)

        # Test if bytes can be passed into array
        actual_bytes = b"\x05\x04\x03\x02\x01\x00"
        actual = ArrayDynamicType(ByteType()).encode(actual_bytes)
        expected = bytes([0, 6, 5, 4, 3, 2, 1, 0])
        # self.assertEqual sometimes has problems with byte comparisons
        assert actual == expected

        actual = ArrayDynamicType(ByteType()).decode(expected)
        expected = [5, 4, 3, 2, 1, 0]
        assert actual == expected

        with self.assertRaises(error.ABIEncodingError) as e:
            ArrayDynamicType(AddressType()).encode([True, False])

    def test_tuple_encoding(self):
        test_cases = [
            (
                ABIType.from_string("()"),
                [],
                b"",
            ),
            (
                ABIType.from_string("(bool[3])"),
                [[True, True, False]],
                bytes([0b11000000]),
            ),
            (
                ABIType.from_string("(bool[])"),
                [[True, True, False]],
                bytes.fromhex("00 02 00 03 C0"),
            ),
            (
                ABIType.from_string("(bool[2],bool[])"),
                [[True, True], [True, True]],
                bytes.fromhex("C0 00 03 00 02 C0"),
            ),
            (
                ABIType.from_string("(bool[],bool[])"),
                [[], []],
                bytes.fromhex("00 04 00 06 00 00 00 00"),
            ),
            (
                ABIType.from_string("(string,bool,bool,bool,bool,string)"),
                ["AB", True, False, True, False, "DE"],
                bytes.fromhex("00 05 A0 00 09 00 02 41 42 00 02 44 45"),
            ),
        ]

        for test_case in test_cases:
            actual = test_case[0].encode(test_case[1])
            expected = test_case[2]
            self.assertEqual(actual, expected)

            # Test decoding
            actual = test_case[0].decode(actual)
            expected = test_case[1]
            self.assertEqual(actual, expected)


class TestABIInteraction(unittest.TestCase):
    def test_method(self):
        # Parse method object from JSON
        test_json = '{"name": "add", "desc": "Calculate the sum of two 64-bit integers", "args": [ { "name": "a", "type": "uint64", "desc": "..." },{ "name": "b", "type": "uint64", "desc": "..." } ], "returns": { "type": "uint128", "desc": "..." } }'
        m = Method.from_json(test_json)
        self.assertEqual(m.get_signature(), "add(uint64,uint64)uint128")
        self.assertEqual(m.get_selector(), b"\x8a\xa3\xb6\x1f")
        self.assertEqual(
            [(a.type) for a in m.args],
            [ABIType.from_string("uint64"), ABIType.from_string("uint64")],
        )
        self.assertEqual(m.get_txn_calls(), 1)

        # Parse method object from string
        test_cases = [
            (
                "add(uint64,uint64)uint128",
                b"\x8a\xa3\xb6\x1f",
                [ABIType.from_string("uint64"), ABIType.from_string("uint64")],
                ABIType.from_string("uint128"),
                1,
            ),
            (
                "tupler((string,uint16),bool)void",
                b"\x3d\x98\xe4\x5d",
                [
                    ABIType.from_string("(string,uint16)"),
                    ABIType.from_string("bool"),
                ],
                "void",
                1,
            ),
            (
                "txcalls(pay,pay,axfer,byte)bool",
                b"\x05\x6d\x2e\xc0",
                ["pay", "pay", "axfer", ABIType.from_string("byte")],
                ABIType.from_string("bool"),
                4,
            ),
            (
                "getter()string",
                b"\xa2\x59\x11\x1d",
                [],
                ABIType.from_string("string"),
                1,
            ),
            (
                "foreigns(account,pay,asset,application,bool)void",
                b"\xbf\xed\xf2\xc1",
                [
                    "account",
                    "pay",
                    "asset",
                    "application",
                    ABIType.from_string("bool"),
                ],
                "void",
                2,
            ),
        ]

        for test_case in test_cases:
            m = Method.from_signature(test_case[0])

            # Check method signature
            self.assertEqual(m.get_signature(), test_case[0])
            # Check selector
            self.assertEqual(m.get_selector(), test_case[1])
            # Check args
            self.assertEqual([(a.type) for a in m.args], test_case[2])
            # Check return
            self.assertEqual(m.returns.type, test_case[3])
            # Check txn calls
            self.assertEqual(m.get_txn_calls(), test_case[4])

    def test_interface(self):
        test_json = '{"name": "Calculator","desc":"This is an example interface","methods": [{ "name": "add", "returns": {"type": "void"}, "args": [ { "name": "a", "type": "uint64", "desc": "..." },{ "name": "b", "type": "uint64", "desc": "..." } ] },{ "name": "multiply", "returns": {"type": "void"}, "args": [ { "name": "a", "type": "uint64", "desc": "..." },{ "name": "b", "type": "uint64", "desc": "..." } ] }]}'
        i = Interface.from_json(test_json)
        self.assertEqual(i.name, "Calculator")
        self.assertEqual(i.desc, "This is an example interface")
        self.assertEqual(
            [m.get_signature() for m in i.methods],
            ["add(uint64,uint64)void", "multiply(uint64,uint64)void"],
        )

    def test_contract(self):
        test_json = '{"name": "Calculator","desc":"This is an example contract","networks":{"wGHE2Pwdvd7S12BL5FaOP20EGYesN73ktiC1qzkkit8=":{"appID":1234},"SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI=":{"appID":5678}}, "methods": [{ "name": "add", "returns": {"type": "void"}, "args": [ { "name": "a", "type": "uint64", "desc": "..." },{ "name": "b", "type": "uint64", "desc": "..." } ] },{ "name": "multiply", "returns": {"type": "void"}, "args": [ { "name": "a", "type": "uint64", "desc": "..." },{ "name": "b", "type": "uint64", "desc": "..." } ] }]}'
        c = Contract.from_json(test_json)
        self.assertEqual(c.name, "Calculator")
        self.assertEqual(c.desc, "This is an example contract")
        self.assertEqual(
            c.networks,
            {
                "wGHE2Pwdvd7S12BL5FaOP20EGYesN73ktiC1qzkkit8=": NetworkInfo(
                    app_id=1234
                ),
                "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI=": NetworkInfo(
                    app_id=5678
                ),
            },
        )
        self.assertEqual(
            [m.get_signature() for m in c.methods],
            ["add(uint64,uint64)void", "multiply(uint64,uint64)void"],
        )
