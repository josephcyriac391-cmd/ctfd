document.addEventListener('DOMContentLoaded', function() {
    // Check if we are on the challenges page
    if (window.location.pathname === '/challenges') {
        
        fetch('/api/v1/team-path/current', {
            headers: {
                'Accept': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success && data.data) {
                const pathInfo = data.data;
                const progressPercent = pathInfo.total_stages > 0 ? (pathInfo.current_stage / pathInfo.total_stages) * 100 : 0;
                
                const pathUI = `
                <div class="row mb-4">
                    <div class="col-md-12">
                        <div class="card" style="border-left: 5px solid ${pathInfo.color || '#007bff'};">
                            <div class="card-body">
                                <h3 class="card-title">YOUR TREASURE PATH</h3>
                                <h5>Path: <strong>${pathInfo.path_name}</strong></h5>
                                <p class="text-muted">${pathInfo.path_description || ''}</p>
                                
                                <div class="mt-3">
                                    <p class="mb-1">Progress: Stage ${pathInfo.current_stage} of ${pathInfo.total_stages}</p>
                                    <div class="progress" style="height: 20px;">
                                        <div class="progress-bar bg-success" role="progressbar" style="width: ${progressPercent}%;" aria-valuenow="${progressPercent}" aria-valuemin="0" aria-valuemax="100"></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                `;
                
                // Find a good place to insert it. Usually above the challenges board.
                // CTFd typically has a div with id 'challenges-board'
                const board = document.getElementById('challenges-board');
                if (board && board.parentElement) {
                    const tempDiv = document.createElement('div');
                    tempDiv.innerHTML = pathUI;
                    board.parentElement.insertBefore(tempDiv.firstElementChild, board);
                }
            } else if (data.success && data.data === null) {
                // Not assigned to a path yet, show token input
                const assignUI = `
                <div class="row mb-4">
                    <div class="col-md-12">
                        <div class="card bg-light">
                            <div class="card-body">
                                <h4 class="card-title">Join a Treasure Path</h4>
                                <p>Enter your team's starting token to begin the treasure hunt.</p>
                                <div class="input-group mb-3" style="max-width: 400px;">
                                    <input type="text" id="path-token-input" class="form-control" placeholder="Token (e.g. ASTHRA_...)">
                                    <div class="input-group-append">
                                        <button class="btn btn-primary" type="button" id="join-path-btn">Join</button>
                                    </div>
                                </div>
                                <div id="path-join-msg"></div>
                            </div>
                        </div>
                    </div>
                </div>
                `;
                
                const board = document.getElementById('challenges-board');
                if (board && board.parentElement) {
                    const tempDiv = document.createElement('div');
                    tempDiv.innerHTML = assignUI;
                    board.parentElement.insertBefore(tempDiv.firstElementChild, board);
                    
                    document.getElementById('join-path-btn').addEventListener('click', function() {
                        const token = document.getElementById('path-token-input').value;
                        if (!token) return;
                        
                        fetch('/team-path/assign', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'CSRF-Token': init.csrfNonce // CTFd typically exposes this globally
                            },
                            body: JSON.stringify({ token: token })
                        })
                        .then(r => r.json())
                        .then(res => {
                            const msgDiv = document.getElementById('path-join-msg');
                            if (res.success) {
                                msgDiv.innerHTML = `<span class="text-success">${res.message}</span>`;
                                setTimeout(() => window.location.reload(), 1000);
                            } else {
                                msgDiv.innerHTML = `<span class="text-danger">${res.error}</span>`;
                            }
                        });
                    });
                }
            }
        })
        .catch(console.error);
    }
});
