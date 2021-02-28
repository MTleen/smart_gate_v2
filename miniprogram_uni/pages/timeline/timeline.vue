<template>
	<view>
		<u-time-line>
			<u-time-line-item nodeTop="0" v-for="item in items">
				<!-- 此处自定义了左边内容，用一个图标替代 -->
				<template v-slot:node>
					<view class="u-node" :style="infos[item.command].style">
						<!-- 此处为uView的icon组件 -->
						<u-icon :name="infos[item.command].icon" color="#fff" :size="24"></u-icon>
					</view>
				</template>
				<template v-slot:content>
					<view>
						<view class="u-order-title">{{infos[item.command].name}}</view>
						<view class="u-order-desc">
							<image :src='item.url' mode="aspectFit"></image>
							<!-- <u-image width="100%" height="500rpx" :src="item.url" mode='aspectFit'>
								<u-loading slot="loading"></u-loading>
							</u-image> -->
						</view>
						<view class="u-order-time">{{item.date}}</view>
					</view>
				</template>
			</u-time-line-item>
		</u-time-line>
	</view>
</template>

<script>
	export default {
		data() {
			return {
				items: [],
				infos: {
					'1': {
						icon: 'checkmark-circle',
						style: "background: #19be6b", 
						name: '开 门'
					},
					'2': {
						icon: 'close-circle',
						style: "background: #ff5555",
						name: '关 门'
					},
				}
			}
		},
		onLoad() {
			const that = this
			uni.request({
				url: 'https://rss.fourieripper.icu:5000/get_history',
				success: (res) => {
					console.log(res)
					if(typeof(res.data) == 'object'){
						var his = []
						for(var i in res.data){
							his.push(JSON.parse(res.data[i]))
						}
						that.items = his
					}else if(res.data == 'error'){
						uni.showToast({
							title: '服务器错误'
						})
					}
				}
			})
		},
		methods: {
			
		}
	}
</script>

<style>
	u-time-line{
		display: block;
		padding: 20rpx 40rpx;
	}
	
	.u-node {
		width: 44rpx;
		height: 44rpx;
		border-radius: 100rpx;
		display: flex;
		justify-content: center;
		align-items: center;
		background: #d0d0d0;
	}
	
	.u-order-title {
		color: #333333;
		font-weight: bold;
		font-size: 28rpx;
	}
	
	.u-order-desc {
		color: rgb(150, 150, 150);
		font-size: 28rpx;
		margin-bottom: 6rpx;
		margin-top: 6rpx;
	}
	
	.u-order-time {
		color: rgb(200, 200, 200);
		font-size: 26rpx;
	}
</style>
