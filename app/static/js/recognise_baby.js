function getBabyAttributes() {
    var s = $("#petId").val();
    if (s.indexOf('petId=') !== -1){
        var petId=s.substr(s.indexOf('petId=') + 6, 19);
    }else{
        var petId = s.replace(/[^0-9]/ig, "");
    }
    console.log(petId);
    if (petId.length !== 19) {
        alert("狗蛋ID不正确");
        return;
    }
    $("#luckyPercentage").html("");

    $("#parents").hide();
    $("#baby").hide();
    $("#father").hide();
    $("#mother").hide();
    $.ajax({
        url: "getBabyAttributes",
        type: "POST",
        dataType: 'json',
        data: {
            petId: petId
        },
        async: true,
        success: function(data) {
            console.log(data);
            setLuckyPercentage(data);
            $("#parents").show();
            setPetDetails('baby', data);
            setPetDetails('father', data.father);
            setPetDetails('mother', data.mother);
        },
        error: function() {
            alert("获取狗蛋信息失败");
        }
    });
}

function setLuckyPercentage(data) {
    var html = '<p>在狗蛋父亲、母亲同为<font color="red" size=5>' + data.father.rareAmount + '稀</font>和<font color="red" size=5>' + data.mother.rareAmount + '稀</font>的繁殖PK中, 你打败了<font color="red" size=5>' + data.luckyPercentage + '</font>的狗主人</p>';
    $("#luckyPercentage").html(html);
}

function setPetDetails(petType, details) {
    $("#" + petType + "RareDegree").html(details.rareDegree);
    $("#" + petType + "Generation").html("第" + details.generation + "代");
    $("#" + petType + "CoolingInterval").html(details.coolingInterval);
    var marketLink = 'https://pet-chain.baidu.com/chain/detail?channel=market&petId=' + details.petId + '&appId=1&validCode=';
    if (petType === 'baby') {
        marketLink = 'https://pet-chain.baidu.com/chain/babyDetail?petId=' + details.petId;
    }
    $("#" + petType + "Name").html("<a href=" + marketLink + " target=\"_blank\">" + details.name + " " + details.id + "</a>");

    $('#' + petType + 'PetUrl').attr("src", details.petUrl);
    $('#' + petType + 'PetUrl').css("background-color", details.bgColor);
    var i = 0;
    var trs = '';
    var tds = '';
    for (var key in details.attributes) {
        attribute = details.attributes[key];
        var name = attribute.name;
        var value = attribute.value;
        var rare = "<font color=\"red\">" + attribute.rare + "</font>";
        td = '<td>' + name + '： ' + value + " " + rare + "</td>";
        tds = tds + td;
        i = i + 1;
        if (i % 2 == 0) {
            trs = trs + '<tr>' + tds + '</tr>';
            tds = '';
        }
    }
    var tbody = '<tbody><tr><td><h5 class="text-left">属性</h5></td><td></td></tr>' + trs + '</tbody>';
    $("#" + petType + "AttributesTable").html(tbody);
    $("#" + petType).show();
}

$("#parents").hide();
$("#baby").hide();
$("#father").hide();
$("#mother").hide();