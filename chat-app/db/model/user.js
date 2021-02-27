const mongoose = require("mongoose");
const Schema = mongoose.Schema;
const passportLocalMongoose = require("passport-local-mongoose");

const USER_IMG = "https://image.shutterstock.com/image-vector/default-avatar-profile-icon-vector-260nw-1745180411.jpg";

const UserSchema = new Schema(
    {
        firstname: { type: String, required: true, trim: true},
        lastname: { type: String, trim: true},
        email: { type: String, lowercase: true, trime: true, index: true, unique: true, required: true },
        profile_pic_url: { type: String, trim: true, default: USER_IMG },
    },
    { timestamps: true }
);

UserSchema.plugin(passportLocalMongoose);

module.exports = mongoose.model("User", UserSchema);