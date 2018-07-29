function getBreedInfo() {
	$.ajax({
		url: "getBreedInfo",
		type: "POST",
		dataType: 'json',
		data: {},
		async: true,
		success: function (data) {
			drawBars(data);
			console.log(data);
		},
		error: function () {
			alert("getBreedInfo error");
		}
	});
}

function drawBars(data_total) {
	// 基于准备好的dom，初始化echarts实例
	for (var i = 0; i < 9; i++) {
		var id = 'breed_' + i;
		var myChart = echarts.init(document.getElementById(id));
		data = data_total[i.toString()];
		console.log(data);

		var option = {
			title: {
				text: echarts.format.addCommas(i) + ' 稀狗狗 (' + data.childrenTotal + ' 条)',
				left: 10
			},
			toolbox: {
				feature: {
					dataZoom: {
						yAxisIndex: false
					},
					saveAsImage: {
						pixelRatio: 2
					}
				}
			},
			tooltip: {
				formatter: function (callBackData) {
					d = callBackData[0];
					var fatherMother = d.name.split("-");
					var father = '父亲：' + fatherMother[0] + '稀';
					var mother = '母亲：' + fatherMother[1] + '稀';

					console.log(d.value)
					console.log(callBackData)
					console.log(data.childrenTotal)
					// TODO
					//var percentage = (d.value / data.childrenTotal * 100).toFixed(2) + '%';
					//return father + '<br/>' + mother + '<br/>' + '后代数量：' + d.value + '<br/>' + '占比：' + percentage + '<br/>';
					return father + '<br/>' + mother + '<br/>' + '后代数量：' + d.value + '<br/>';
				},
				trigger: 'axis',
				axisPointer: {
					type: 'shadow'
				}
			},
			grid: {
				bottom: 90
			},
			dataZoom: [{
					type: 'inside'
				}, {
					type: 'slider'
				}
			],
			xAxis: {
				data: data.fatherMother,
				silent: false,
				splitLine: {
					show: false
				},
				splitArea: {
					show: false
				}
			},
			yAxis: {
				splitArea: {
					show: false
				}
			},
			series: [{
					type: 'bar',
					data: data.childrenAmount,
					// Set `large` for large data amount
					large: true
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
getBreedInfo()
