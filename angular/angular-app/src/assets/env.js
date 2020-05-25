(function (window) {
  window["env"] = window["env"] || {};

  // Environment variables
  window["env"]["ANGULAR_PRODUCTION"] = "true";
  window["env"]["ANGULAR_DJANGO_API_URL"] =
    "http://localhost:8000/searchapp/api";
  window["env"]["ANGULAR_DJANGO_API_GLOSSARY_URL"] =
    "http://localhost:8000/glossary/api";
  window["env"]["ANGULAR_DJANGO_API_ADMIN_URL"] =
    "http://localhost:8000/admin/api";
  window["env"]["ANGULAR_DJANGO_AUTH_URL"] = "http://localhost:8000/auth";
  window["env"]["ANGULAR_GOOGLE_CLIENT_ID"] =
    "540501250122-2k39tbh973rc7ufpl2nioor6muejkvok.apps.googleusercontent.com";
  window["env"]["ANGULAR_DJANGO_CLIENT_ID"] =
    "iLGzC0VKWPG5nrlGEByWRO2zo5gXn1gTzKGVHWUa";
  window["env"]["ANGULAR_DJANGO_CLIENT_SECRET"] =
    "vLY4j1po4bb0LfvXwEB5j0EkxuWROQOFtFDt6FrRd74ITsPUHUwhyjQAzlC0JcWqVl4GxrytaWip6zeONW5KPtmNbMQnijfFJFCZ7lnDxvzdstKGbJXMtYS9BLk6GzR2";

  // window["env"]["ANGULAR_DJANGO_API_URL"] =
  //   "https://django.dgfisma.crosslang.com/searchapp/api";
  // window["env"]["ANGULAR_DJANGO_API_ADMIN_URL"] =
  //   "https://django.dgfisma.crosslang.com/admin/api";
  // window["env"]["ANGULAR_DJANGO_AUTH_URL"] =
  //   "https://django.dgfisma.crosslang.com/auth";
})(this);
