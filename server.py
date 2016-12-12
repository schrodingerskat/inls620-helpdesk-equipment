from flask import Flask, render_template, make_response, redirect
from flask.ext.restful import Api, Resource, reqparse, abort

import json
# import string
# import random
# from datetime import datetime

# Load data from JSON 'database'
with open('data.json') as data:
    data = json.load(data)
