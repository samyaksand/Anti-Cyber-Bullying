const express = require('express');
const router = express.Router();

const Connection = require('../db/model/connection');
const MSG = require("../db/model/msg");
const auth = require('../services/auth/authenticate');

router.get('/msg', auth.authenticateUser, async (req, res, next) => {
    try {
        const connections = await Connection.find({})
            .sort({ updatedAt: 1 })
            .populate("user_id");
        
        res.render("msg/index", {
            layout: "./layouts/msg",
            connections: connections,
        });
    } catch (err) {
        next(err);
    }
});

router.get('/msg/chat/:uid', auth.authenticateUser, async (req, res, next) => {
  try {
    const U1_ID = req.user._id;
    const U2_ID = req.params.uid;

    const msgs = await MSG.find({
      $or: [
        {
          $and: [{ sender_id: U1_ID }, { receiver_id: U2_ID }],
        },
        {
          $and: [{ sender_id: U2_ID }, { receiver_id: U1_ID }],
        },
      ],
    }).sort({ updatedAt: 1 });

    res.status(200);
    res.json(msgs);
  } catch (err) {
    next(err);
  }
});
module.exports = router;