import os


class TokenType:  # all possible token types in a JSON string
    STRING = 'STRING'
    NUMBER = 'NUMBER'
    FALSE = 'FALSE'
    TRUE = 'TRUE'
    NULL = 'NULL'
    LEFTCURLY = 'LEFTCURLY'
    RIGHTCURLY = 'RIGHTCURLY'
    LEFTSQUARE = 'LEFTSQUARE'
    RIGHTSQUARE = 'RIGHTSQUARE'
    COMMA = 'COMMA'
    COLON = 'COLON'
    EOF = 'EOF'


class Token:  # represents a token with a type and a value
    def __init__(self, TokenType, value):
        self.type = TokenType
        self.value = value

class TokenDFA:
    def __init__(self):
        self.states = ['q0', 'q1', 'q2', 'q3', 'q4', 'q_accept', 'q_error',
                       'q_array_value', 'q_array_start', 'q_object_in_array']
        self.current_state = 'q0'  # initial state
        self.accepting_states = ['q_accept']  # final state
        self.stack = []  # stack used to handle nested objects/arrays

        # Update transitions to handle objects in arrays better
        self.transitions = {
            ('q0', TokenType.LEFTCURLY): 'q1',  # start of JSON object
            ('q1', TokenType.STRING): 'q2',  # key in the JSON object
            ('q2', TokenType.COLON): 'q3',  # colon following the key
            ('q3', TokenType.LEFTCURLY): 'q0',  # start of nested object
            ('q3', TokenType.STRING): 'q4',
            ('q3', TokenType.NUMBER): 'q4',
            ('q3', TokenType.TRUE): 'q4',
            ('q3', TokenType.FALSE): 'q4',
            ('q3', TokenType.NULL): 'q4',
            ('q3', TokenType.LEFTSQUARE): 'q_array_start',  # Start of a list
            ('q4', TokenType.COMMA): 'q1',  # Another key-value pair in the object
            ('q4', TokenType.RIGHTCURLY): 'q_accept',  # End of JSON object

            # Array transitions
            ('q_array_start', TokenType.STRING): 'q_array_value',
            ('q_array_start', TokenType.NUMBER): 'q_array_value',
            ('q_array_start', TokenType.TRUE): 'q_array_value',
            ('q_array_start', TokenType.FALSE): 'q_array_value',
            ('q_array_start', TokenType.NULL): 'q_array_value',
            ('q_array_start', TokenType.LEFTCURLY): 'q1',  # Start of object in array
            ('q_array_value', TokenType.COMMA): 'q_array_start', # Start of another value
            ('q_array_value', TokenType.RIGHTSQUARE): 'q4',  # end of the list

            # object completion and commas transitions
            ('q_accept', TokenType.COMMA): 'q1',  # possible object to follow
            ('q_accept', TokenType.RIGHTCURLY): 'q_accept',  # closer of a nested object
            ('q_accept', TokenType.EOF): 'q_accept',
        }

    def transition(self, token):
        key = (self.current_state, token.type)

        if token.type == TokenType.LEFTCURLY:
            self.stack.append(('object', self.current_state))  # if we see the start of an object, push the value to the stack
            self.current_state = 'q1'

        elif token.type == TokenType.LEFTSQUARE:
            self.stack.append(('array', self.current_state))  # if we see the start of an list, push the value to the stack
            self.current_state = 'q_array_start'

        elif token.type == TokenType.RIGHTCURLY:
            if self.stack: # if the stack isnt empty
                stack_type, prev_state = self.stack.pop()  # if we see the end of a list, pop the value from the stack
                if stack_type == 'object':
                    if prev_state == 'q_array_start':  # if we were inside an array, move to the array value state
                        self.current_state = 'q_array_value'
                    elif prev_state == 'q3':  # if it was a regular key value pair, move to the regular value state
                        self.current_state = 'q4'
                    else:  #  its complet otherwise
                        self.current_state = 'q_accept'
                else:  # if the popped item isn't an object, it's an error
                    self.current_state = 'q_error'
            else:
                self.current_state = 'q_accept'

        elif token.type == TokenType.RIGHTSQUARE:
            if self.stack:  # if the stack isnt empty
                stack_type, prev_state = self.stack.pop()  # if we see the end of a object, pop the value from the stack
                if stack_type == 'array':
                    if prev_state == 'q3':
                        self.current_state = 'q4'
                    else:
                        self.current_state = prev_state
                else:
                    self.current_state = 'q_error'
            else:
                self.current_state = 'q_error'

        elif token.type == TokenType.COMMA:
            if self.current_state == 'q4' or 'q_accept':  # comma in these states means another value
                self.current_state = 'q1'
            elif self.current_state == 'q_array_value':  # comma aver an array value means the start of another value
                self.current_state = 'q_array_start'
            else:  # comma is unexpected
                print(f"Error: Unexpected token '{token.type}' in state '{self.current_state}'")
                self.current_state = 'q_error'

        elif key in self.transitions:  # handle other transitions using the transition table
            self.current_state = self.transitions[key]

        else:
            print(f"Error: Unexpected token '{token.type}' in state '{self.current_state}'")
            self.current_state = 'q_error'

    def is_accepting(self):
        # for it to be valid JSON, we need to be in a final state, and have an empty stack
        return self.current_state in self.accepting_states and not self.stack

    def is_error(self):  # check if the current state is in the error state
        return self.current_state == 'q_error'


class JSONScanner:
    def __init__(self, input_text):
        self.input_text = input_text
        self.position = 0  # start of input string
        self.tokenized_list = []  # empty list of tokens
        self.current_char = self.input_text[self.position] if self.input_text else None
        self.error = False

    def advance(self):  # this method looks ahead in the input, allowing us to decide our next move
        self.position += 1
        if self.position >= len(self.input_text):
            self.current_char = None
        else:
            self.current_char = self.input_text[self.position]


        # Token Recognition for Strings
    def recognize_string(self):
        result = ''
        start_position = self.position
        self.advance()  # Skip first quote
        while self.current_char is not None:
            if self.current_char == '"':  # End of string
                self.advance()  # Skip closing quote
                return Token(TokenType.STRING, result)  # return string token
            result += self.current_char
            self.advance()
        # If no closing quote is found
        self.error = True
        print(f"Error: Unclosed string starting at position {start_position}")
        return None

    # Token Recognition for Numbers
    def recognize_number(self):
        result = ''
        while self.current_char is not None and self.current_char.isdigit():
            result += self.current_char
            self.advance()
        return Token(TokenType.NUMBER, result)  # return number token

    # Token Recognition for Boolean and Null
    def recognize_bool_and_null(self):
        literals = {
            "true": Token(TokenType.TRUE, "true"),
            "false": Token(TokenType.FALSE, "false"),
            "null": Token(TokenType.NULL, "null")
        }
        for literal, token in literals.items():
            if self.input_text[self.position:self.position + len(literal)] == literal:
                self.position += len(literal)  # advance the position after recognizing the literal
                self.current_char = self.input_text[self.position] if self.position < len(self.input_text) else None
                return token  # return whatever token was recognized
        self.error = True
        print(f"Unrecognized literal starting at position {self.position}")
        return None

    # Token Recognition for Punctuation
    def recognize_punctuation(self):
        punctuations = {
            '{': TokenType.LEFTCURLY,
            '}': TokenType.RIGHTCURLY,
            '[': TokenType.LEFTSQUARE,
            ']': TokenType.RIGHTSQUARE,
            ':': TokenType.COLON,
            ',': TokenType.COMMA
        }
        token_type = punctuations.get(self.current_char)  # check if the punctuation is valid
        if token_type:  # if valid
            char = self.current_char
            self.advance()
            return Token(token_type, char)
        self.error = True
        print(f"Unrecognized punctuation: {self.current_char}")
        return None

    def tokenize(self):
        while self.current_char is not None:
            position = self.position
            if self.current_char.isspace():
                self.advance()
            elif self.current_char.isdigit():
                token = self.recognize_number()  # recognize number
                if token:
                    self.tokenized_list.append(token)
                else:
                    break
            elif self.current_char in ['n', 't', 'f']:  # maybe boolean or null
                token = self.recognize_bool_and_null()
                if token:
                    self.tokenized_list.append(token)
                else:
                    break
            elif self.current_char in ['{', '}', '[', ']', ':', ',']:  # maybe punctuation
                token = self.recognize_punctuation()
                if token:
                    self.tokenized_list.append(token)
                else:
                    break
            elif self.current_char == '"':  # recognize start of a string
                token = self.recognize_string()
                if token:
                    self.tokenized_list.append(token)
                else:
                    break
            else:  # unrecognized
                self.error = True
                print(f"Unrecognized input '{self.current_char}' starting at position: {position}")
                break
        if not self.error:
            self.tokenized_list.append(Token(TokenType.EOF, -1))  # add EOF to show its the end of input
        return None if self.error else self.tokenized_list


def run_test_files(input_folder = 'input_folder', output_folder = 'output_folder'):

    if not os.path.exists('input_folder'):  # check if folder exists
        print("Input folder not found")
        return
    if not os.path.exists('output_folder'):  # check if folder exists
        print("Output folder not found")
        return

    for i in range(1, 11):
        input_file_name = os.path.join(input_folder, f"input{i:02d}.txt")  # get names of files, like input01.txt, input02.txt, etc
        output_file_name = os.path.join(output_folder, f"output{i:02d}.txt")  # get names of files, like output01.txt, output02.txt, etc

        if os.path.isfile(input_file_name):  # check if file exists
            with open(input_file_name, 'r') as input_file:
                input_text = input_file.read()

            scanner = JSONScanner(input_text)
            token_list = scanner.tokenize()
            if not token_list:
                print(f"Error found in {input_file_name} during tokenization.")
                continue

            with open(output_file_name, 'w') as output_file:
                dfa = TokenDFA()
                for idx, token in enumerate(token_list):
                    dfa.transition(token)
                    if dfa.is_error():
                        output_file.write(f"Error at token {idx}: Unexpected token '{token.type}' ")
                        output_file.write("Cannot proceed further until resolved")
                        break

                if not dfa.is_accepting():
                    output_file.write("Error: Token sequence did not end in an accepting state ")
                    output_file.write("Cannot proceed further until resolved")
                    continue

                # If the DFA accepts the token sequence, we can confirm it's valid JSON
                for token in token_list:
                    output_file.write(f"<{token.type}, {token.value}>\n")


def main():
    run_test_files()


if __name__ == "__main__":
    main()