        document.addEventListener('DOMContentLoaded', () => {
            const main = document.querySelector('main');
            main.style.opacity = '0';
            main.style.transform = 'scale(0.9)';
            main.style.transition = 'all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275)';
            
            setTimeout(() => {
                main.style.opacity = '1';
                main.style.transform = 'scale(1)';
            }, 100);
        });