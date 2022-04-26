(function (window) {
  window["env"] = window["env"] || {};

  // Environment variables
  window["env"]["ANGULAR_PRODUCTION"] = "true";
  window["env"]["ANGULAR_DJANGO_API_URL"] =
    "http://localhost:8000/searchapp/api";
  window["env"]["ANGULAR_DJANGO_API_GLOSSARY_URL"] =
    "http://localhost:8000/glossary/api";
  window["env"]["ANGULAR_DJANGO_API_RO_URL"] =
    "http://localhost:8000/obligations/api";
  window["env"]["ANGULAR_DJANGO_API_CPSV_URL"] =
    "http://localhost:8000/cpsv/api";
  window["env"]["ANGULAR_DJANGO_API_GLOSSARY_ANNOTATIONS_URL"] =
    "http://localhost:8000/glossary/api/annotations";
    window["env"]["ANGULAR_DJANGO_API_RO_ANNOTATIONS_URL"] =
    "http://localhost:8000/obligations/api/annotations";
  window["env"]["ANGULAR_DJANGO_API_ADMIN_URL"] =
    "http://localhost:8000/admin/api";
  window["env"]["ANGULAR_DJANGO_AUTH_URL"] = "http://localhost:8000/auth";
  window["env"]["ANGULAR_GOOGLE_CLIENT_ID"] =
    ".apps.googleusercontent.com";
  window["env"]["ANGULAR_DJANGO_CLIENT_ID"] =
    "";
  window["env"]["ANGULAR_DJANGO_CLIENT_SECRET"] =
    "";

  // window["env"]["ANGULAR_DJANGO_API_URL"] =
  //   "https://django.dgfisma.crosslang.com/searchapp/api";
  // window["env"]["ANGULAR_DJANGO_API_ADMIN_URL"] =
  //   "https://django.dgfisma.crosslang.com/admin/api";
  // window["env"]["ANGULAR_DJANGO_AUTH_URL"] =
  //   "https://django.dgfisma.crosslang.com/auth";
})(this);
