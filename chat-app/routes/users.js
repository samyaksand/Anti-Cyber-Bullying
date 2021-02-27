var express = require('express');
var router = express.Router();
const passport = require('passport');
require('../services/auth/oauth');


router.get("/auth/google/success", (req, res, next) => {
  req.flash("success", "Successfully authenticated using Google Accounts");
  res.redirect("/");
});

router.get("/auth/google/failure", (req, res, next) => {
  req.flash("danger", "somthing went wrong, authentication failed!");
  res.redirect("/");
});

router.get(
  "/auth/google/callback",
  passport.authenticate("google", {
    successRedirect: "/auth/google/success",
    failureRedirect: "/auth/google/failure",
  })
);

router.get(
  "/auth/google",
  passport.authenticate("google", {
    scope: ["email", "profile"],
  })
);

router.get("/logout", (req, res, next) => {
  if (req.session && req.user) {
    req.logout();
    req.flash("danger", "You are Successfully logged out!");
  } else {
    req.flash("danger", "You are already logged out!");
  }
  res.redirect("/");
});

module.exports = router;