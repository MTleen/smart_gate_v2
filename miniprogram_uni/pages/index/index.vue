<template>
	<view class="content">
		<u-toast ref="uToast" />
		<view class="container" v-if="canIUse && !hasUserInfo">
			<u-button type='info' :ripple="true" open-type="getUserInfo" @getuserinfo="getUserInfo">授 权 登 陆</u-button>
		</view>
		<view v-else style="margin-top: 30rpx;">
			<u-divider fontSize='35' half-width='250'>大 门</u-divider>
			<view class="container2">
				<u-button type='primary' :ripple='true' plain @click='sendCommand("0")'>开 门</u-button>
				<u-button type='primary' :ripple='true' plain @click='sendCommand("1")'>关 门</u-button>
				<u-button type='primary' :ripple='true' plain @click='sendCommand("2")'>暂 停</u-button>
			</view>
			<u-divider fontSize='35' half-width='250'>车库门 2</u-divider>
			<view class="container2">
				<u-button type='success' :ripple='true' plain @click='sendCommand("4")'>开 门</u-button>
				<u-button type='success' :ripple='true' plain @click='sendCommand("5")'>关 门</u-button>
				<u-button type='success' :ripple='true' plain @click='sendCommand("6")'>暂 停</u-button>
			</view>
			<u-cell-group>
				<u-cell-item :title="mode" :arrow="false" icon='home-fill' hover-class='null'>
					<u-switch slot="right-icon" v-model="checked" :loading='loading' @change='change'></u-switch>
				</u-cell-item>
			</u-cell-group>
		</view>
	</view>
</template>

<script>
	export default {
		data() {
			return {
				userInfo: {},
				hasUserInfo: false,
				canIUse: uni.canIUse('button.open-type.getUserInfo'),
				checked: false,
				loading: false,			
				mode: "手动模式",
				whiteList: []
			}
		},
		onLoad() {
			var app = getApp()
			console.log(app.globalData)
			if (app.globalData.userInfo) {
				this.userInfo = app.globalData.userInfo
				this.hasUserInfo = true
			} else if (this.canIUse) {
				// 由于 getUserInfo 是网络请求，可能会在 Page.onLoad 之后才返回
				// 所以此处加入 callback 以防止这种情况
				uni.userInfoReadyCallback = res => {
					this.userInfo = res.userInfo
					this.hasUserInfo = true
			  }
			} else {
			  // 在没有 open-type=getUserInfo 版本的兼容处理
				uni.getUserInfo({
					success: res => {
						console.log(res)
						app.globalData.userInfo = res.userInfo
						this.userInfo = res.userInfo
						this.hasUserInfo = true
					}
				})
			}
			
			// 获取门控模式
			const that = this
			uni.request({
			  url: 'https://rss.fourieripper.icu:5000/get_mode',
			  success: function(res){
			    if(res.statusCode == 200){
					that.mode = res.data
					that.checked = res.data == '手动模式'? false:true
			    }
			  }
			})
			// 获取白名单
			uni.request({
			  url: 'https://rss.fourieripper.icu:5000/get_whitelist',
			  success: function(res){
			    console.log(res)
				that.whiteList = res.data
			  }
			})
		},
		methods: {
			getUserInfo(e) {
				// console.log(e)
				getApp().globalData.userInfo = e.detail.userInfo
				this.userInfo = e.detail.userInfo
				this.hasUserInfo = true
			},
			sendCommand(command) {
				console.log(command)
				uni.request({
					url: 'https://rss.fourieripper.icu:5000/send_command',
					data: {
						operation: command
					},
					success: res => {
						if(res.statusCode == 200){
							this.$refs.uToast.show({
								title: '执行成功',
								duration: 1500,
								type: 'success',
								icon: 'true'
							})
						}
					},
					fail: (res) => {
						show_alert()
					}
				})
			},
			show_alert(){
				this.$refs.uToast.show({
					title: '执行失败，联系小胡',
					duration: 1500,
					type: 'error',
					icon: 'true'
				})
			},
			change(status){
				var that = this
				this.loading = true
				if(status){
					uni.request({
						url: 'https://rss.fourieripper.icu:5000/set_mode',
						data: {
						  mode: '1'
						},
						success: res => {
						  console.log(res)
						  if(res.statusCode == 200){
						    that.mode = '自动模式'
						    that.loading = false
						  }
						},
						fail: () => {
							that.loading = false
							show_alert()
						}
					})
				}else{
					uni.request({
						url: 'https://rss.fourieripper.icu:5000/set_mode',
						data: {
						  mode: '0'
						},
						success: res => {
						  console.log(res)
						  if(res.statusCode == 200){
						    that.mode = '手动模式'
						    that.loading = false
						  }
						},
						fail: () => {
							that.loading = false
							show_alert()
						}
					})
				}
			}
		}
	}
</script>

<style>
	.container {
		margin-top: 30%;
	}
	
	.container2{
		display: flex;
		flex-direction: row;
		justify-content: space-around;
		flex-wrap: wrap;
		/* padding: 20rpx 0; */
		/* height: 250rpx; */
		align-content: space-around;
		margin-bottom: 100rpx;
		margin-top: 30rpx;
	}
	
	.content {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
	}

	.text-area {
		display: flex;
		justify-content: center;
	}

	.title {
		font-size: 36rpx;
		color: #8f8f94;
	}
</style>
