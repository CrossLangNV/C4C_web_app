(function (window) {
  window["env"] = window["env"] || {};

  // Environment variables
  window["env"]["ANGULAR_PRODUCTION"] = "${ANGULAR_PRODUCTION}";
  window["env"]["ANGULAR_DJANGO_API_URL"] = "${ANGULAR_DJANGO_API_URL}";
  window["env"]["ANGULAR_DJANGO_API_GLOSSARY_URL"] = "${ANGULAR_DJANGO_API_GLOSSARY_URL}";
  window["env"]["ANGULAR_DJANGO_API_RO_URL"] = "${ANGULAR_DJANGO_API_RO_URL}";
  window["env"]["ANGULAR_DJANGO_API_ADMIN_URL"] =
    "${ANGULAR_DJANGO_API_ADMIN_URL}";
  window["env"]["ANGULAR_DJANGO_AUTH_URL"] = "${ANGULAR_DJANGO_AUTH_URL}";
  window["env"]["ANGULAR_GOOGLE_CLIENT_ID"] = "${ANGULAR_GOOGLE_CLIENT_ID}";
  window["env"]["ANGULAR_DJANGO_CLIENT_ID"] = "${ANGULAR_DJANGO_CLIENT_ID}";
  window["env"]["ANGULAR_DJANGO_CLIENT_SECRET"] =
    "${ANGULAR_DJANGO_CLIENT_SECRET}";
})(this);
