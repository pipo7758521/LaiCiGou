var app = new Vue({
    delimiters: ['${', '}'],
    el: '#app',
    data: {
        queryPetId: '',
        queryTwinsDetails: [],
        attributes: {},
        info: '',
        finish: false
    },
    methods: {
        queryTwins: function() {
            var self = this;
            self.finish = false;
            self.info = "查询中，请稍等...";
            if (self.queryPetId.indexOf('petId=') !== -1) {
                self.queryPetId = self.queryPetId.substr(self.queryPetId.indexOf('petId=') + 6, 19);
            } else {
                self.queryPetId = self.queryPetId.replace(/[^0-9]/ig, "");
            }
            if (self.queryPetId.length !== 19) {
                self.info = "无效的狗狗petId， 请输入正确的19位petId";
                return;
            }
            console.log(petId);
            $.ajax({
                url: "queryTwins",
                type: "POST",
                dataType: 'json',
                data: {
                    petId: self.queryPetId
                },
                async: true,
                success: function(data) {
                    self.finish = true;
                    if (data.info) {
                        self.info = data.info;
                    } else {
                        self.info = "";
                        self.queryTwinsDetails = data;
                        var a = new Array();
                        self.attributes = {};
                        var index = 0;
                        for (var i in self.queryTwinsDetails.attributes) {
                            a.push(self.queryTwinsDetails.attributes[i]);
                            index = index + 1;
                            if (index % 2 == 0) {
                                self.attributes[index + ""] = a;
                                a = [];
                            }
                        }
                    }
                },
                error: function() {
                    alert("queryTwins error");
                }
            });
        }
    }
})