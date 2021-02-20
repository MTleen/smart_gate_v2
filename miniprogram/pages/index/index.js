// index.js
// 获取应用实例
const app = getApp()

Page({
  data: {
    userInfo: {},
    hasUserInfo: false,
    canIUse: wx.canIUse('button.open-type.getUserInfo'),
    mode: "自动模式",
    nextMode: "手动模式",
    modes: {
      "自动模式": 1,
      "手动模式": 0
    }
  },
  // 事件处理函数
  bindViewTap() {
    wx.navigateTo({
      url: '../logs/logs'
    })
  },
  sendCommand(event) {
    var command = event.currentTarget.dataset.param
    wx.request({
      url: 'https://rss.fourieripper.icu:5000/send_command',
      data: {
        operation: command
      },
      success: function(res){
        console.log(res)
        if(res.statusCode == 200){
          wx.showToast({
            title: '执行成功',
            icon: 'success',
            duration: 1500
          })
        }else{
          wx.showModal({
            title: '出错',
            content: '指令执行出错'
          })
        }
      }
    })
  },

  changeMode(event){
    const that = this
    console.log(event)
    wx.request({
      url: 'https://rss.fourieripper.icu:5000/set_mode',
      data: {
        mode: this.data.modes[this.data.nextMode]
      },
      success: function(res){
        console.log(res)
        if(res.statusCode == 200){
          wx.showToast({
            title: '模式修改成功',
            icon: 'success'
          })
          var temp = that.data.mode
          that.setData({'mode': that.data.nextMode, 'nextMode': temp})
          // this.setData('nextMode', temp)
        }
      }
    })
  },

  onLoad() {
    if (app.globalData.userInfo) {
      this.setData({
        userInfo: app.globalData.userInfo,
        hasUserInfo: true
      })
    } else if (this.data.canIUse) {
      // 由于 getUserInfo 是网络请求，可能会在 Page.onLoad 之后才返回
      // 所以此处加入 callback 以防止这种情况
      app.userInfoReadyCallback = res => {
        this.setData({
          userInfo: res.userInfo,
          hasUserInfo: true
        })
      }
    } else {
      // 在没有 open-type=getUserInfo 版本的兼容处理
      console.log(1)
      wx.getUserInfo({
        success: res => {
          console.log(res)
          app.globalData.userInfo = res.userInfo
          this.setData({
            userInfo: res.userInfo,
            hasUserInfo: true
          })
        }
      })
    }

    // 获取门控模式
    const that = this
    wx.request({
      url: 'https://rss.fourieripper.icu:5000/get_mode',
      success: function(res){
        if(res.statusCode == 200){
          that.setData({'mode': res.data, 'nextMode': res.data == '手动模式'? '自动模式':'手动模式'})
        }
      }
    })
    // 获取白名单
    wx.request({
      url: 'https://rss.fourieripper.icu:5000/get_whitelist',
      success: function(res){
        console.log(res)
        that.setData({'white_list': res.data})
      }
    })
  },
  getUserInfo(e) {
    // console.log(e)
    app.globalData.userInfo = e.detail.userInfo
    this.setData({
      userInfo: e.detail.userInfo,
      hasUserInfo: true
    })
  }
})
