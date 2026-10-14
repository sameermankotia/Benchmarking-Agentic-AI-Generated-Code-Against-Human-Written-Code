
from flask_pair import FlaskPair, Response, Blueprint

app = FlaskPair()

@app.route("/", methods=["GET"])
def home(request):
    return Response("Welcome to Flask Pair!")

@app.route("/hello/<name>", methods=["GET"])
def hello(request):
    name = request.path.split("/")[-1]
    return Response(f"Hello, {name}!")

blueprint = Blueprint("example", "/example")

@blueprint.route("/info", methods=["GET"])
def info(request):
    return Response("This is an example blueprint.")

blueprint.register(app)

if __name__ == "__main__":
    app.run()