(function (window) {
  window["env"] = window["env"] || {};

  // Environment variables
  window["env"]["ANGULAR_PRODUCTION"] = "false";
  window["env"]["ANGULAR_DJANGO_API_URL"] =
    "http://localhost:8000/searchapp/api";
  window["env"]["ANGULAR_DJANGO_API_ADMIN_URL"] =
    "http://localhost:8000/admin/api";
  window["env"]["ANGULAR_DJANGO_AUTH_URL"] = "http://localhost:8000/auth";
  window["env"]["ANGULAR_GOOGLE_CLIENT_ID"] =
    "540501250122-2k39tbh973rc7ufpl2nioor6muejkvok.apps.googleusercontent.com";
  window["env"]["ANGULAR_DJANGO_CLIENT_ID"] =
    "***REMOVED***";
  window["env"]["ANGULAR_DJANGO_CLIENT_SECRET"] =
    "***REMOVED***;

  // window["env"]["ANGULAR_DJANGO_API_URL"] =
  //   "https://django.dgfisma.crosslang.com/searchapp/api";
  // window["env"]["ANGULAR_DJANGO_API_ADMIN_URL"] =
  //   "https://django.dgfisma.crosslang.com/admin/api";
  // window["env"]["ANGULAR_DJANGO_AUTH_URL"] =
  //   "https://django.dgfisma.crosslang.com/auth";
})(this);