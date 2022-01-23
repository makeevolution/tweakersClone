from visualizeScrapedData import app, server

if __name__ == "__main__":
    app.init_app(server)
    app.run_server(host="0.0.0.0",port=5000)
    