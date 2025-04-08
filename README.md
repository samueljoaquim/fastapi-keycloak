I've created a Python sample application to show how to integrate a `FastAPI` application with `Keycloak`. The source code is available at my [Github repo](https://github.com/samueljoaquim/fastapi-keycloak). It's by no means a complete or perfectly executed application, consider this more a proof of concept that doesn't care as much for usability and beauty :D.

To run it, first you need to install the dependencies:
```bash
pipenv install --dev
```
> If you don't have `pipenv` installed in your environment, you can install it by running `pip install pipenv`.

Make sure you create a client for your app in Keycloak. If you are using `http://localhost:8000/` as your app's URL, the redirect URL in Keycloak should be `http://localhost:8000/auth/redirect`. Also, you need to create two roles in your client: `read-data` and `write-data`. Then, create two groups with the following roles associated: 
* `fastapi-keycloak-read` - assing the `read-data` role to it in `Role mapping`.
* `fastapi-keycloak-write` - assing both `read-data` and `write-data` in `Role mapping`.

Add your main user to the `fastapi-keycloak-write` group, and create another user that doesn't belong to any of these groups.

Now, you need to create a `.env` file for your environment in the root of the project (you can use `.env.example` as well, just copy it to `.env` and edit it):

```bash
APP_FORCE_HTTPS=false

KEYCLOAK_SERVER_URL=http://localhost:8080/
KEYCLOAK_CLIENT_ID=CLIENT_ID
KEYCLOAK_CLIENT_SECRET=CLIENT_SECRET
KEYCLOAK_REALM=internal

KEYCLOAK_ADMIN_CLIENT_ID=ADMIN_CLIENT_ID
KEYCLOAK_ADMIN_CLIENT_SECRET=ADMIN_CLIENT_SECRET
KEYCLOAK_ADMIN_REALM=master

REDIS_HOST=localhost
REDIS_PORT=6379
```
> This app uses an unauthenticated `redis` server for caching the user session info. If you don't have Redis running, you can use Podman / Docker to spin a new instance: `docker run --name redis -p 6379:6379 -d redis`

`APP_FORCE_HTTPS` should be false, unless you intend to run it in an HTTPS environment. The `KEYCLOAK_` (without the `ADMIN_`) entries should match those from your Keycloak client. The `KEYCLOAK_ADMIN_` ones enable a feature for being able to add an user to a realm group to exemplify access management through Keycloak's management API. If you want to test it, use the `admin-cli` client info from your master realm (client id will be "admin-cli", and you can grab the secret from the credentials tab).

Once everything is set, you should now be able to execute the app:
```
pipenv run fastapi run ./main.py
```

### Under the hood
This is how the application is structured:
* `routers/`: These are the application endpoints.
  * `api.py`: The API endpoints that should be protected from unauthenticated / unauthorized access.
  * `auth.py`: The authentication endpoints.
  * `default.py`: The root (`/`) path. This should just redirect the user to the `auth/login` endpoint, which in turn will redirect the user to Keycloak's login page.
* `services/`: The application services.
  * `auth.py`: Authentication services.
  * `keycloak.py`: Keycloak admin services for demonstrating Keycloak's API abilities.
* `static/`: The application HTML page.
* `utils/session.py`: Several utilities used to handle session login / logout.

### How it works
The first function of interest is in `routes/auth.py`, which is `login_redirect`. It will use the `AuthService.login_redirect` method. This method uses the `KeycloakOpenID.auth_url` method to generate the redirect URL for Keycloak login, setting parameters such as the apps redirect URL on successful login, the scope and other things.

Once the user is authenticated in Keycloak, the `redirect` function in `routes/auth.py` is called. It receives a code from the Keycloak server in the URL query, which will then be used to get an access token from Keycloak (think of this as a two way handshake). Once we get the access token, we set it as a cookie, so that this access token is provided to the application in every new request. Also, note that we are calling `save_session_data` in `AuthService.get_access_token`. This will save a few things that we will use later in Redis. 

Now, we are ready for the last redirect, which is to send the user to the actual home page in `pages/home.html`. This page will use javascript's `fetch` to validate the user and get user information, like the first name:

<img src="https://www.sjoaquim.com/screenshot-fastapi-logged-in.png" style="width: 50%; min-width: 300px" />

### The Session
In the `utils/session.py` file, there's a function called `session_data`. This function is called every time a user makes a new request that requires an authenticated user. It does quite a lot of things: validates the token using the `python-keycloak` library; if the token is expired, tries to refresh it with Keycloak; verified that that token has already stablished a session within the application (which should be available in redis); finally, it returns the saved session data.

This function is used as a dependency injection for the `verify_role` function in the same file. The later validates that the user has a given role, and fails if the user doesn't match the required role. This function is also used as a dependency injection in the API router (check the `api_router` module variable in `routers/api.py`). This means that every route under this router requires the read role (at least) before being able to proceed.

There's also the `add_user_to_group` function, which required the write role. Let's explore that.

### Keycloak API for adding a user to a group
If you click on `Logout`, you should be redirected to the login page once more, since the access token was revoked through the use of `KeycloakOpenID.logout`. Now, remember that we created another user that didn't belong to any groups? If you try to login with that user, you'll get a JSON response saying:
```json
{"detail": "User doesn't have access to the application"}
```
So, that proves that the role validation is working. But remember that your other user had read and write roles. The write role is used in this application to add an user to the read group. So let's login again with the previous user. If you get stuck in the user without access, you can go to Keycloak and, under `Sessions`, identify the session for your user, click on the three vertical dots and sign the user out.

Now, you are ready to sign in again with the write-enabled user. Once you do that, you'll see that you have the `username` text field, along with a button saying `Add User to Default Group`. Type the second user's username and click on the button. If no error message was displayed, you should have added your user to the `fastapi-keycloak-read` group. To verify that, you can go to the user's detail page in Keycloak and make sure that the `fastapi-keycloak-read` group is displayed under the `Groups` tab.

And that's it! If you try to login again, you should be able to see the application's page with your other user. And, just to make sure that the write role works, try to add any user into the `username` text field and clicking the button. You should see an error message saying `User doesn't have access to the resource`. And that's it for role validation and Keycloak management API!
