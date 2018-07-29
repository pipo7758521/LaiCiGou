//userName =  window.location.href.split("/").pop();
//console.log(userName);
var app = new Vue({
    delimiters: ['${', '}'],
    el: '#app',
    data: {
        userName: 'query',
        userAvailableQueryFilter: ['全部', '在售'],
        enableUpdateMyPets:false,
        pages: 0,
        info: '',
        petType: '全部',
        attributes: [],
        pets: []
    },
    created: function () {
        // 下面代码作为极其简单的用户区分（非注册方式！！！！！！！）
        this.userName = window.location.href.split("/").pop();
        if (this.userName === 'query') {
            // 匿名用户
            this.userAvailableQueryFilter = ['全部', '在售']; // 匿名用户

            // 不显示更新我的狗狗数据按钮
            this.enableUpdateMyPets = false;
        } else {
            // 默认后台已有的用户
            this.userAvailableQueryFilter = ['全部', '在售', '收藏待购买', '我的珍藏', '我的狗狗'];

            // 显示更新我的狗狗数据按钮
            this.enableUpdateMyPets = true;
        }
        console.log(this.userName)
        this.queryAttributes();
    },
    methods: {
        queryAttributes: function () {
            var self = this;
            $.ajax({
                url: "queryAttributes",
                type: "POST",
                dataType: 'json',
                data: {},
                async: true,
                success: function (data) {
                    self.attributes = data;
                    console.log(self.attributes);
                },
                error: function () {
                    self.info = "抱歉，服务器出了点问题";
                }
            });
        },
        initPagination: function () {
            var self = this;
            var obj = $('#pagination').twbsPagination({
                first: "首",
                prev: "上",
                next: "下",
                last: "末",
                totalPages: self.pages,
                visiblePages: 5,
                onPageClick: function (event, page) {
                    self.queryPetsOfPage(page);
                }
            });
            console.info(obj.data());
        },
        getPages: function () {
            var self = this;
            self.pets = [];
            // 解绑
            $('#pagination').twbsPagination('destroy');
            self.info = "查询中请稍后...";
            $.ajax({
                url: "getPages",
                type: "POST",
                dataType: 'json',
                data: {
                    userName: self.userName,
                    petType: self.petType,
                    attributes: self.attributes
                },
                async: true,
                success: function (data) {
                    self.pages = data.pages;
                    self.initPagination();
                },
                error: function () {
                    self.info = "抱歉，服务器出了点问题";
                }
            });
        },
        queryPetsOfPage: function (pageNo) {
            console.log('queryPetsOfPage');
            var self = this;
            self.pets = [];
            self.info = "查询中请稍后...";
            $.ajax({
                url: "queryPetsOfPage",
                type: "POST",
                dataType: 'json',
                data: {
                    userName: self.userName,
                    pageNo: pageNo,
                    petType: self.petType,
                    attributes: self.attributes
                },
                async: true,
                success: function (data) {
                    self.info = "查询完毕";
                    self.pets = data.pets;
                    if (self.pets.length === 0) {
                        self.info = "不存在该属性的狗狗";
                    }
                },
                error: function () {
                    self.info = "抱歉，服务器出了点问题";
                }
            });
        },
        collect: function (petId, operation) {
            console.log(petId);
            var self = this;
            $.ajax({
                url: "collect",
                type: "POST",
                dataType: 'json',
                data: {
                    userName: self.userName,
                    petType: self.petType,
                    operation: operation,
                    petId: petId
                },
                async: true,
                success: function (data) {
                    self.updatePetOperation(petId, data.featureOperation)
                },
                error: function () {
                    self.info = "操作失败";
                }
            });
        },
        updatePetOperation: function (petId, operation) {
            for (var i = 0; i < this.pets.length; i++) {
                if (this.pets[i].petId === petId) {
                    this.pets[i].operation = operation;
                    break;
                }
            }
        },
        updateMyPets: function () {
            var self = this;
            $.ajax({
                url: "updateMyPets",
                type: "POST",
                dataType: 'json',
                data: {
                    userName: self.userName
                },
                async: true,
                success: function (data) {
                    self.info = data.info;
                },
                error: function () {
                    self.info = "操作失败";
                }
            });
        }

    }
})