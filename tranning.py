import pandas as pd
from textblob import TextBlob

a = "this is a good boy"
b = TextBlob(a)

print(b.sentiment.polarity)
