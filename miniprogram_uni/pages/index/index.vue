<template>
	<view class="content">
		<view class="container" v-if="canIUse && !hasUserInfo">
			<u-button type='info' :ripple="true" open-type="getUserInfo" @getuserinfo="getUserInfo">授 权 登 陆</u-button>
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
				mode: "自动模式",
				nextMode: "手动模式",
				modes: {
				  "自动模式": 1,
				  "手动模式": 0
				}
			}
		},
		onLoad() {
			if (globalData.userInfo) {
				this.userInfo = uni.globalData.userInfo
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
				console.log(1)
				uni.getUserInfo({
					success: res => {
						console.log(res)
						uni.globalData.userInfo = res.userInfo
						this.userInfo = res.userInfo
						this.hasUserInfo = true
					}
				})
			}
		},
		methods: {

		}
	}
</script>

<style>
	.container {
		margin-top: 30%;
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
