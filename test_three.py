import streamlit as st
import streamlit.components.v1 as components

def three_js_car():
    html_code = """
    <div id="container" style="width: 100%; height: 400px;"></div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script>
        const container = document.getElementById('container');
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0xf0f2f6);
        
        const camera = new THREE.PerspectiveCamera(75, container.clientWidth / 400, 0.1, 1000);
        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(container.clientWidth, 400);
        container.appendChild(renderer.domElement);

        // Lights
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
        scene.add(ambientLight);
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(5, 5, 5);
        scene.add(directionalLight);

        // Simple 3D Car Body
        const bodyGeometry = new THREE.BoxGeometry(4, 1, 2);
        const bodyMaterial = new THREE.MeshPhongMaterial({ color: 0x667eea });
        const body = new THREE.Mesh(bodyGeometry, bodyMaterial);
        scene.add(body);

        // Cabin
        const cabinGeometry = new THREE.BoxGeometry(2, 0.8, 1.8);
        const cabinMaterial = new THREE.MeshPhongMaterial({ color: 0x333333 });
        const cabin = new THREE.Mesh(cabinGeometry, cabinMaterial);
        cabin.position.y = 0.9;
        cabin.position.x = -0.5;
        scene.add(cabin);

        // Wheels
        const wheelGeometry = new THREE.CylinderGeometry(0.5, 0.5, 0.4, 32);
        const wheelMaterial = new THREE.MeshPhongMaterial({ color: 0x111111 });
        
        const wheels = [];
        const wheelPositions = [
            [1.5, -0.5, 1], [1.5, -0.5, -1],
            [-1.5, -0.5, 1], [-1.5, -0.5, -1]
        ];

        wheelPositions.forEach(pos => {
            const wheel = new THREE.Mesh(wheelGeometry, wheelMaterial);
            wheel.position.set(...pos);
            wheel.rotation.x = Math.PI / 2;
            scene.add(wheel);
            wheels.push(wheel);
        });

        camera.position.z = 7;
        camera.position.y = 2;
        camera.lookAt(0, 0, 0);

        function animate() {
            requestAnimationFrame(animate);
            scene.rotation.y += 0.01;
            renderer.render(scene, camera);
        }
        animate();

        window.addEventListener('resize', () => {
            const width = container.clientWidth;
            camera.aspect = width / 400;
            camera.updateProjectionMatrix();
            renderer.setSize(width, 400);
        });
    </script>
    """
    components.html(html_code, height=400)

st.title("Three.js car test")
three_js_car()
