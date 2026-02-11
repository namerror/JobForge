import os

TOP_N = int(os.getenv("TOP_N", 5)) # how many skills to return per category, in the future could be broken down by category or customized in request body
METHOD = os.getenv("METHOD", "baseline")
