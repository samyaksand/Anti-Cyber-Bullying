const mongoose = require('mongoose');

// mongoose.connect(
//     process.env.DATABASE_URI,
//     { useNewUrlParser: true, useUnifiedTopology: true },
//     () => {console.log("Connected to DB");
// });

mongoose.connect(
    process.env.DATABASE_URI, 
    {
    useNewUrlParser: true,
    useCreateIndex: true,
    useUnifiedTopology: true},
    () => console.log("Connected to DB"));