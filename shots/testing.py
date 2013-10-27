from tokenizer import Tokenizer

t = Tokenizer("../templates/index.html")
t.tokenize()

for line in t.lines:
	for token in line:
		print token
