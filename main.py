import os
from flask import Flask, render_template
from api import create_app

app = create_app()

@app.route("/")
def index():
    return render_template('index.html')

if __name__ == '__main__':
    port=int(os.environ.get('PORT', 8080))
    app.run(debug=True, host='0.0.0.0', port=port)
