from app.admin import routes

if __name__ == '__main__':
    res = routes.test_instagram_connection(user='admin')
    print(res)
