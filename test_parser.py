import unittest
from parser import parse_hoi4_save_from_string, Tokenizer, Token, Parser

class TestHOI4Parser(unittest.TestCase):
    
    def test_tokenizer_basic(self):
        """Test basic tokenizer functionality."""
        content = "key=value"
        tokenizer = Tokenizer(content)
        tokens = tokenizer.tokenize()
        
        self.assertEqual(len(tokens), 3)
        self.assertEqual(tokens[0].type, Token.TYPE_IDENTIFIER)
        self.assertEqual(tokens[0].value, "key")
        self.assertEqual(tokens[1].type, Token.TYPE_EQUALS)
        self.assertEqual(tokens[2].type, Token.TYPE_IDENTIFIER)
        self.assertEqual(tokens[2].value, "value")
    
    def test_tokenizer_braces(self):
        """Test tokenizer with braces."""
        content = "object={key=value}"
        tokenizer = Tokenizer(content)
        tokens = tokenizer.tokenize()
        
        self.assertEqual(len(tokens), 7)
        self.assertEqual(tokens[0].type, Token.TYPE_IDENTIFIER)
        self.assertEqual(tokens[0].value, "object")
        self.assertEqual(tokens[1].type, Token.TYPE_EQUALS)
        self.assertEqual(tokens[2].type, Token.TYPE_OPEN_BRACE)
        self.assertEqual(tokens[3].type, Token.TYPE_IDENTIFIER)
        self.assertEqual(tokens[3].value, "key")
        self.assertEqual(tokens[4].type, Token.TYPE_EQUALS)
        self.assertEqual(tokens[5].type, Token.TYPE_IDENTIFIER)
        self.assertEqual(tokens[5].value, "value")
        self.assertEqual(tokens[6].type, Token.TYPE_CLOSE_BRACE)
    
    def test_parser_basic(self):
        """Test basic parser functionality."""
        content = "key=value"
        data = parse_hoi4_save_from_string(content)
        
        self.assertIsInstance(data, dict)
        self.assertEqual(data.get("key"), "value")
    
    def test_parser_nested(self):
        """Test parser with nested objects."""
        content = "object={key1=value1 key2=value2}"
        data = parse_hoi4_save_from_string(content)
        
        self.assertIsInstance(data, dict)
        self.assertIsInstance(data.get("object"), dict)
        self.assertEqual(data["object"].get("key1"), "value1")
        self.assertEqual(data["object"].get("key2"), "value2")
    
    def test_parser_nested_deep(self):
        """Test parser with deeply nested objects."""
        content = """
        root={
            level1={
                level2={
                    level3={
                        key=value
                    }
                }
            }
        }
        """
        data = parse_hoi4_save_from_string(content)
        
        self.assertIsInstance(data, dict)
        self.assertIsInstance(data.get("root"), dict)
        self.assertIsInstance(data["root"].get("level1"), dict)
        self.assertIsInstance(data["root"]["level1"].get("level2"), dict)
        self.assertIsInstance(data["root"]["level1"]["level2"].get("level3"), dict)
        self.assertEqual(data["root"]["level1"]["level2"]["level3"].get("key"), "value")
    
    def test_parser_multiple_values(self):
        """Test parser with multiple values for the same key."""
        content = """
        list={
            item=value1
            item=value2
            item=value3
        }
        """
        data = parse_hoi4_save_from_string(content)
        
        self.assertIsInstance(data, dict)
        self.assertIsInstance(data.get("list"), dict)
        self.assertIsInstance(data["list"].get("item"), list)
        self.assertEqual(len(data["list"]["item"]), 3)
        self.assertEqual(data["list"]["item"][0], "value1")
        self.assertEqual(data["list"]["item"][1], "value2")
        self.assertEqual(data["list"]["item"][2], "value3")
    
    def test_parser_numeric_values(self):
        """Test parser with numeric values."""
        content = """
        values={
            integer=123
            float=123.456
            string=abc
        }
        """
        data = parse_hoi4_save_from_string(content)
        
        self.assertIsInstance(data, dict)
        self.assertIsInstance(data.get("values"), dict)
        self.assertEqual(data["values"].get("integer"), 123)
        self.assertEqual(data["values"].get("float"), 123.456)
        self.assertEqual(data["values"].get("string"), "abc")
    
    def test_parser_complex(self):
        """Test parser with a more complex example."""
        content = """
        production={
            available_equipments={
                equipment={ id=5 type=70 }
                equipment={ id=6 type=70 }
            }
            dirty=no
            military_lines={
                id={ id=783 type=56 }
                produced=0.074
                active_factories=10
                priority=0
                amount=-1
                speed=36.235
                resources={
                    steel={ 10.000 0.000}
                    coal={ 20.000 0.000}
                }
            }
        }
        """
        data = parse_hoi4_save_from_string(content)
        
        self.assertIsInstance(data, dict)
        self.assertIsInstance(data.get("production"), dict)
        self.assertIsInstance(data["production"].get("available_equipments"), dict)
        self.assertIsInstance(data["production"]["available_equipments"].get("equipment"), list)
        self.assertEqual(len(data["production"]["available_equipments"]["equipment"]), 2)
        self.assertEqual(data["production"].get("dirty"), "no")
        self.assertIsInstance(data["production"].get("military_lines"), dict)
        self.assertEqual(data["production"]["military_lines"].get("produced"), 0.074)
        self.assertEqual(data["production"]["military_lines"].get("active_factories"), 10)
        self.assertIsInstance(data["production"]["military_lines"].get("resources"), dict)
        self.assertIsInstance(data["production"]["military_lines"]["resources"].get("steel"), dict)
        self.assertIsInstance(data["production"]["military_lines"]["resources"].get("coal"), dict)

if __name__ == "__main__":
    unittest.main() 