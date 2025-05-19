from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello():
    return "<h1>Hello, World!</h1><p>This is a minimal Flask app running on Render!</p>"

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)
