function getData() {
	$.ajax({
		url: "getData",
		type: "POST",
		dataType: 'json',
		data: {},
		async: true,
		success: function (data) {
			drawPies(data['results']);
			console.log(data['results']);
		},
		error: function () {
			alert("getData error");
		}
	});
}

function drawPies(data) {
	// 基于准备好的dom，初始化echarts实例
	for (var i = 0; i < data.length; i++) {
	    var id='pie_'+i;
	    var myChart = echarts.init(document.getElementById(id));
		pieData = data[i];
		option = {
			title: {
				text: pieData['text'],
				//subtext: '2018',
				x: 'center'
			},
			tooltip: {
				trigger: 'item',
				formatter: "{a} <br/>{b} : {c} ({d}%)"
			},

			series: [{
					name: pieData['text'],
					type: 'pie',
					radius: '50%',
					center: ['50%', '50%'],
					data: pieData['data'],
					itemStyle: {
						emphasis: {
							shadowBlur: 10,
							shadowOffsetX: 0,
							shadowColor: 'rgba(0, 0, 0, 0.5)'
						}
					}
				}
			]
		};

		// 使用刚指定的配置项和数据显示图表。
		myChart.setOption(option);
		window.onresize = myChart.resize;
		// 使用刚指定的配置项和数据显示图表。
		myChart.setOption(option);
	}
}

getData();