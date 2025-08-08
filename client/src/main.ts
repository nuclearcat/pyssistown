import Phaser from 'phaser'

const config: Phaser.Types.Core.GameConfig = {
  type: Phaser.AUTO,
  width: 800,
  height: 600,
  scene: {
    preload() {},
    create() {},
    update() {},
  },
}

new Phaser.Game(config)
