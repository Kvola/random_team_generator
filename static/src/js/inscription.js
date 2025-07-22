document.addEventListener('DOMContentLoaded', function() {
    const simpleSelects = document.querySelectorAll('.searchable-select');
    simpleSelects.forEach(function(select) {
        try {
            new TomSelect(select, {
                create: false,
                sortField: { field: "text", direction: "asc" },
                allowEmptyOption: true,
                placeholder: "Sélectionner...",
                searchField: ['text'],
                maxItems: select.hasAttribute('multiple') ? null : 1,
                plugins: select.hasAttribute('multiple') ? ['remove_button'] : [],
                render: {
                    no_results: function(data, escape) {
                        return '<div class="no-options">Aucune option trouvée pour "' + escape(data.input) + '"</div>';
                    }
                }
            });
        } catch (error) {
            console.warn('Erreur lors de l\'initialisation de TomSelect:', error);
        }
    });

    initializeMultiSelect();

    function initializeMultiSelect() {
        const multiSelects = document.querySelectorAll('.multi-select-container');
        
        multiSelects.forEach(container => {
            const fieldName = container.dataset.name;
            const hiddenInput = document.querySelector(`input[name="${fieldName}"]`);
            
            if (!hiddenInput) {
                console.warn(`Champ caché non trouvé pour: ${fieldName}`);
                return;
            }

            const selectedTags = container.querySelector('.selected-tags');
            const placeholder = container.querySelector('.placeholder');
            const dropdown = container.querySelector('.options-dropdown');
            const searchInput = container.querySelector('.search-input');
            const optionsList = container.querySelector('.options-list');
            const options = container.querySelectorAll('.option-item');
            const dropdownArrow = container.querySelector('.dropdown-arrow');

            let selectedValues = [];
            let isOpen = false;

            initializeValues();

            function initializeValues() {
                const initialValue = hiddenInput.value.trim();
                if (initialValue) {
                    const initialValues = initialValue.split(',')
                        .map(val => val.trim())
                        .filter(val => val !== '');
                    
                    initialValues.forEach(val => {
                        const option = container.querySelector(`.option-item[data-value="${val}"]`);
                        if (option) {
                            const text = option.dataset.text || option.textContent.trim();
                            selectedValues.push(val);
                            createTag(val, text);
                            updateOptionState(val, true);
                        }
                    });
                }

                const dataSelected = hiddenInput.dataset.selected;
                if (dataSelected && selectedValues.length === 0) {
                    const dataValues = dataSelected.split(',')
                        .map(val => val.trim())
                        .filter(val => val !== '');
                    
                    dataValues.forEach(val => {
                        const option = container.querySelector(`.option-item[data-value="${val}"]`);
                        if (option) {
                            const text = option.dataset.text || option.textContent.trim();
                            selectedValues.push(val);
                            createTag(val, text);
                            updateOptionState(val, true);
                        }
                    });
                }

                updateHiddenInput();
                updatePlaceholder();
            }

            container.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                if (!e.target.closest('.remove-tag')) {
                    toggleDropdown();
                }
            });

            document.addEventListener('click', function(e) {
                if (!container.contains(e.target)) {
                    closeDropdown();
                }
            });

            container.addEventListener('keydown', function(e) {
                switch(e.key) {
                    case 'Enter':
                    case ' ':
                        e.preventDefault();
                        if (!isOpen) {
                            openDropdown();
                        }
                        break;
                    case 'Escape':
                        e.preventDefault();
                        closeDropdown();
                        break;
                    case 'ArrowDown':
                        e.preventDefault();
                        if (!isOpen) {
                            openDropdown();
                        } else {
                            focusNextOption();
                        }
                        break;
                    case 'ArrowUp':
                        e.preventDefault();
                        if (isOpen) {
                            focusPreviousOption();
                        }
                        break;
                }
            });

            if (searchInput) {
                searchInput.addEventListener('input', function() {
                    filterOptions(this.value.toLowerCase());
                });

                searchInput.addEventListener('keydown', function(e) {
                    if (e.key === 'Escape') {
                        closeDropdown();
                    }
                });
            }

            options.forEach(option => {
                option.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    const value = this.dataset.value;
                    const text = this.dataset.text || this.textContent.trim();
                    
                    if (selectedValues.includes(value)) {
                        removeValue(value);
                    } else {
                        addValue(value, text);
                    }
                });

                option.addEventListener('keydown', function(e) {
                    if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        this.click();
                    }
                });
            });

            function toggleDropdown() {
                if (isOpen) {
                    closeDropdown();
                } else {
                    openDropdown();
                }
            }

            function openDropdown() {
                if (isOpen) return;
                
                isOpen = true;
                dropdown.classList.add('show');
                container.classList.add('active');
                
                if (searchInput) {
                    setTimeout(() => {
                        searchInput.focus();
                    }, 100);
                }

                container.dispatchEvent(new CustomEvent('multiSelectOpen'));
            }

            function closeDropdown() {
                if (!isOpen) return;
                
                isOpen = false;
                dropdown.classList.remove('show');
                container.classList.remove('active');
                
                if (searchInput) {
                    searchInput.value = '';
                    filterOptions('');
                }

                container.dispatchEvent(new CustomEvent('multiSelectClose'));
            }

            function addValue(value, text) {
                if (!selectedValues.includes(value)) {
                    selectedValues.push(value);
                    createTag(value, text);
                    updateHiddenInput();
                    updatePlaceholder();
                    updateOptionState(value, true);
                    
                    container.dispatchEvent(new CustomEvent('multiSelectAdd', {
                        detail: { value, text }
                    }));
                }
            }

            function removeValue(value) {
                const index = selectedValues.indexOf(value);
                if (index > -1) {
                    const removedText = getTextForValue(value);
                    selectedValues.splice(index, 1);
                    removeTag(value);
                    updateHiddenInput();
                    updatePlaceholder();
                    updateOptionState(value, false);
                    
                    container.dispatchEvent(new CustomEvent('multiSelectRemove', {
                        detail: { value, text: removedText }
                    }));
                }
            }

            function createTag(value, text) {
                const tag = document.createElement('div');
                tag.className = 'selected-tag';
                tag.dataset.value = value;
                tag.setAttribute('role', 'button');
                tag.setAttribute('aria-label', `Supprimer ${text}`);
                
                tag.innerHTML = `
                    <span class="tag-text">${escapeHtml(text)}</span>
                    <span class="remove-tag" data-value="${value}" title="Supprimer" aria-label="Supprimer ${text}">×</span>
                `;

                const removeBtn = tag.querySelector('.remove-tag');
                removeBtn.addEventListener('click', function(e) {
                    e.stopPropagation();
                    e.preventDefault();
                    removeValue(value);
                });

                removeBtn.addEventListener('keydown', function(e) {
                    if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        removeValue(value);
                    }
                });

                selectedTags.appendChild(tag);
            }

            function removeTag(value) {
                const tag = selectedTags.querySelector(`[data-value="${value}"]`);
                if (tag) {
                    tag.style.animation = 'tagDisappear 0.3s ease forwards';
                    setTimeout(() => {
                        if (tag.parentNode) {
                            tag.remove();
                        }
                    }, 300);
                }
            }

            function updateHiddenInput() {
                hiddenInput.value = selectedValues.join(',');
                hiddenInput.dispatchEvent(new Event('change', { bubbles: true }));
            }

            function updatePlaceholder() {
                if (placeholder) {
                    placeholder.style.display = selectedValues.length === 0 ? 'block' : 'none';
                }
                
                const count = selectedValues.length;
                container.setAttribute('aria-label', 
                    count === 0 ? 'Aucun élément sélectionné' : 
                    count === 1 ? '1 élément sélectionné' : 
                    `${count} éléments sélectionnés`);
            }

            function updateOptionState(value, selected) {
                const option = container.querySelector(`.option-item[data-value="${value}"]`);
                if (option) {
                    if (selected) {
                        option.classList.add('selected');
                        option.setAttribute('aria-selected', 'true');
                    } else {
                        option.classList.remove('selected');
                        option.setAttribute('aria-selected', 'false');
                    }
                }
            }

            function filterOptions(searchTerm) {
                if (!optionsList) return;
                
                let visibleCount = 0;
                
                options.forEach(option => {
                    const text = (option.dataset.text || option.textContent).toLowerCase();
                    const matches = text.includes(searchTerm);
                    
                    option.style.display = matches ? 'flex' : 'none';
                    if (matches) visibleCount++;
                });

                manageNoOptionsMessage(visibleCount === 0);
            }

            function manageNoOptionsMessage(show) {
                let noOptionsDiv = optionsList.querySelector('.no-options');
                
                if (show && !noOptionsDiv) {
                    noOptionsDiv = document.createElement('div');
                    noOptionsDiv.className = 'no-options';
                    noOptionsDiv.textContent = 'Aucune option trouvée';
                    optionsList.appendChild(noOptionsDiv);
                } else if (!show && noOptionsDiv) {
                    noOptionsDiv.remove();
                }
            }

            function getTextForValue(value) {
                const option = container.querySelector(`.option-item[data-value="${value}"]`);
                return option ? (option.dataset.text || option.textContent.trim()) : value;
            }

            function focusNextOption() {
                const visibleOptions = Array.from(options).filter(opt => 
                    opt.style.display !== 'none');
                const focused = document.activeElement;
                const currentIndex = visibleOptions.indexOf(focused);
                
                if (currentIndex < visibleOptions.length - 1) {
                    visibleOptions[currentIndex + 1].focus();
                }
            }

            function focusPreviousOption() {
                const visibleOptions = Array.from(options).filter(opt => 
                    opt.style.display !== 'none');
                const focused = document.activeElement;
                const currentIndex = visibleOptions.indexOf(focused);
                
                if (currentIndex > 0) {
                    visibleOptions[currentIndex - 1].focus();
                }
            }

            updatePlaceholder();
            
            options.forEach(option => {
                option.setAttribute('tabindex', '0');
                option.setAttribute('role', 'option');
                option.setAttribute('aria-selected', 'false');
            });

            container.setAttribute('tabindex', '0');
            container.setAttribute('role', 'combobox');
            container.setAttribute('aria-expanded', 'false');
            container.setAttribute('aria-haspopup', 'listbox');
        });
    }

    function escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', function(e) {
            let isValid = true;
            const errors = [];

            const requiredFields = form.querySelectorAll('[required]');
            requiredFields.forEach(field => {
                const value = field.value.trim();
                
                if (!value) {
                    isValid = false;
                    errors.push(`Le champ "${getFieldLabel(field)}" est obligatoire.`);
                    field.classList.add('is-invalid');
                    
                    field.addEventListener('input', function() {
                        this.classList.remove('is-invalid');
                    }, { once: true });
                }
            });

            const birthDay = document.querySelector('[name="birth_day"]');
            const birthMonth = document.querySelector('[name="birth_month"]');
            const birthYear = document.querySelector('[name="birth_year"]');

            if (birthDay && birthMonth && birthYear) {
                if (!birthDay.value || !birthMonth.value || !birthYear.value) {
                    isValid = false;
                    errors.push('Veuillez remplir tous les champs de la date de naissance.');
                    
                    [birthDay, birthMonth, birthYear].forEach(field => {
                        if (!field.value) {
                            field.classList.add('is-invalid');
                        }
                    });
                } else {
                    const day = parseInt(birthDay.value);
                    const month = parseInt(birthMonth.value);
                    const year = parseInt(birthYear.value);
                    
                    const date = new Date(year, month - 1, day);
                    const today = new Date();
                    
                    if (date.getDate() !== day || 
                        date.getMonth() !== month - 1 || 
                        date.getFullYear() !== year) {
                        isValid = false;
                        errors.push('La date de naissance n\'est pas valide.');
                        [birthDay, birthMonth, birthYear].forEach(field => {
                            field.classList.add('is-invalid');
                        });
                    } else if (date > today) {
                        isValid = false;
                        errors.push('La date de naissance ne peut pas être dans le futur.');
                        [birthDay, birthMonth, birthYear].forEach(field => {
                            field.classList.add('is-invalid');
                        });
                    }
                }
            }

            const termsCheckbox = document.querySelector('#accept_terms');
            if (termsCheckbox && !termsCheckbox.checked) {
                isValid = false;
                errors.push('Vous devez accepter les conditions d\'utilisation pour continuer.');
                termsCheckbox.classList.add('is-invalid');
            }

            const requiredMultiSelects = form.querySelectorAll('.multi-select-container[data-required="true"]');
            requiredMultiSelects.forEach(container => {
                const fieldName = container.dataset.name;
                const hiddenInput = document.querySelector(`input[name="${fieldName}"]`);
                
                if (hiddenInput && !hiddenInput.value.trim()) {
                    isValid = false;
                    const label = getFieldLabel(hiddenInput) || container.dataset.label || fieldName;
                    errors.push(`Le champ "${label}" est obligatoire.`);
                    container.classList.add('is-invalid');
                }
            });

            if (!isValid) {
                e.preventDefault();
                
                if (errors.length > 0) {
                    alert('Erreurs de validation :\n\n' + errors.join('\n'));
                }

                const firstInvalid = form.querySelector('.is-invalid');
                if (firstInvalid) {
                    firstInvalid.scrollIntoView({
                        behavior: 'smooth',
                        block: 'center'
                    });
                    
                    if (firstInvalid.focus) {
                        setTimeout(() => firstInvalid.focus(), 500);
                    }
                }
            } else {
                const submitBtn = form.querySelector('button[type="submit"]');
                if (submitBtn) {
                    const originalText = submitBtn.innerHTML;
                    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Envoi en cours...';
                    submitBtn.disabled = true;
                    
                    setTimeout(() => {
                        if (submitBtn.disabled) {
                            submitBtn.innerHTML = originalText;
                            submitBtn.disabled = false;
                        }
                    }, 30000);
                }
            }
        });
    }

    function getFieldLabel(field) {
        const label = form.querySelector(`label[for="${field.id}"]`);
        if (label) {
            return label.textContent.replace(' *', '').trim();
        }
        
        const name = field.name || field.dataset.name;
        return name ? name.replace(/[_-]/g, ' ') : 'Champ inconnu';
    }

    function handleDateSelectorsResize() {
        const dateSelectors = document.querySelectorAll('.date-selectors');
        dateSelectors.forEach(selector => {
            if (window.innerWidth <= 768) {
                selector.classList.add('mobile-layout');
            } else {
                selector.classList.remove('mobile-layout');
            }
        });
    }

    handleDateSelectorsResize();
    window.addEventListener('resize', debounce(handleDateSelectorsResize, 250));

    const card = document.querySelector('.card');
    if (card) {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            card.style.transition = 'all 0.5s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, 100);
    }

    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    const style = document.createElement('style');
    style.textContent = `
        @keyframes tagDisappear {
            from { 
                transform: scale(1) translateY(0); 
                opacity: 1; 
            }
            to { 
                transform: scale(0.8) translateY(-10px); 
                opacity: 0; 
            }
        }
        
        .is-invalid {
            border-color: #dc3545 !important;
            box-shadow: 0 0 0 0.2rem rgba(220, 53, 69, 0.25) !important;
        }
    `;
    document.head.appendChild(style);

    console.log('Multi-select script initialisé avec succès');
});