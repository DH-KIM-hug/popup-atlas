import './styles.css';
import { Game } from './game/Game';

const canvas = document.querySelector<HTMLCanvasElement>('#game-canvas');
if (!canvas) throw new Error('Missing #game-canvas element.');

const game = new Game(canvas);
void game.start();

const hint = document.getElementById('hint');
const hide = () => hint?.classList.add('gone');
window.addEventListener('keydown', hide, { once: true });
canvas.addEventListener('pointerdown', hide, { once: true });

if (import.meta.hot) {
  import.meta.hot.dispose(() => game.dispose());
}
