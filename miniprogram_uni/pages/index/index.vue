<template>
	<view class="content">
		<view class="container">
			<u-button type='info' :ripple="true">授 权 登 陆</u-button>
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
