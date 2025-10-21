from app import create_app


def main():
    app = create_app()
    if not app:
        print("Failed to create Flask application")
        return

    host, port = app.config["ENDPOINT"].split(":")
    app.run(host=host, port=int(port), debug=app.config["ENABLE_DEBUG"])


if __name__ == "__main__":
    main()
