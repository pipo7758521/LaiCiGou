function convertId() {
    var s = $("#shortId").val();
    var shortId = s.replace(/[^0-9]/ig, "");
    console.log(shortId);
    if (shortId.length !== 8) {
        alert("ID不正确");
        return;
    }
    $('#result').html('');
    $.ajax({
        url: "convertId",
        type: "POST",
        dataType: 'json',
        data: {
            shortId: shortId
        },
        async: true,
        success: function(data) {
            if (data.petId != null) {
                var marketLink = 'https://pet-chain.baidu.com/chain/detail?channel=market&petId=' + data.petId + '&appId=1&validCode=';
                var breedLink = 'https://pet-chain.baidu.com/chain/detail?channel=breed&petId=' + data.petId + '&appId=1&validCode=';
                $('#result').html('市场地址：<a href="' + marketLink + '">' + marketLink + '</a>' + '<br>' + '繁殖地址：<a href="' + breedLink + '">' + breedLink + '</a>');
            } else {
                $('#result').html('<font color="red">没有找到对应的长19位ID</font>');
            }
            console.log(data);
        },
        error: function() {
            alert("转换失败");
        }
    });
}
$('#result').html('');