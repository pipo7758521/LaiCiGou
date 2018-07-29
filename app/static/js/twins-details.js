id = window.location.pathname.replace('/twinsDetails/', '');
var app = new Vue({
    delimiters: ['${', '}'],
    el: '#app',
    data: {
        attributes: {},
        twinsDetails: {},
        finish:false
    },
    created: function() {
        this.queryTwins();
    },
    methods: {
        queryTwins: function() {
            var self = this;
            self.finish = false;
            $.ajax({
                url: "getDetails",
                type: "POST",
                dataType: 'json',
                data: {
                    id: id
                },
                async: true,
                success: function(data) {
                    self.finish = true;
                    self.twinsDetails = data;
                    var a = new Array();
                    self.attributes = {};
                    var index = 0;
                    for (var i in self.twinsDetails.attributes) {
                        a.push(self.twinsDetails.attributes[i]);
                        index = index + 1;
                        if (index % 2 == 0) {
                            self.attributes[index + ""] = a;
                            a = [];
                        }
                    }
                },
                error: function() {
                    alert("getDetails error");
                }
            });
        }

    }
})