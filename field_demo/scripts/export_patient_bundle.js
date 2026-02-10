/**
 * Export Patient Bundle - ZIP utility for ASHA Field Demo
 * Creates downloadable JSON bundle with all patient data and images
 */

async function exportPatientBundle(patientId) {
    try {
        console.log(`Exporting patient bundle for: ${patientId}`);

        // Get patient data
        const patient = await getFromStore('patients', patientId);
        if (!patient) {
            throw new Error('Patient not found');
        }

        // Get all visits for this patient
        const visits = await queryStoreByIndex('visits', 'patientId', patientId);

        // Get images for each visit
        const visitsWithImages = [];
        for (const visit of visits) {
            const images = await queryStoreByIndex('images', 'visitId', visit.id);
            visitsWithImages.push({
                ...visit,
                images: images.map(img => ({
                    id: img.id,
                    data: img.data,
                    uploadedAt: img.uploadedAt
                }))
            });
        }

        // Create export bundle
        const bundle = {
            version: '1.0.0',
            exportDate: new Date().toISOString(),
            exportedBy: 'ASHA Field Demo',
            patient: {
                ...patient,
                exportNote: 'Complete patient record with all visits and medical images'
            },
            visits: visitsWithImages,
            statistics: {
                totalVisits: visits.length,
                riskLevels: {
                    high: visits.filter(v => v.riskLevel === 'High').length,
                    medium: visits.filter(v => v.riskLevel === 'Medium').length,
                    low: visits.filter(v => v.riskLevel === 'Low').length
                },
                dateRange: {
                    first: visits.length > 0 ? visits[visits.length - 1].visitDate : null,
                    last: visits.length > 0 ? visits[0].visitDate : null
                }
            },
            metadata: {
                totalImages: visitsWithImages.reduce((sum, v) => sum + v.images.length, 0),
                bundleSize: 'calculated_on_download',
                checksum: generateSimpleChecksum(patient.id + patient.name)
            }
        };

        // Convert to JSON string
        const jsonStr = JSON.stringify(bundle, null, 2);
        const blob = new Blob([jsonStr], { type: 'application/json' });

        // Calculate actual size
        bundle.metadata.bundleSize = formatFileSize(blob.size);

        // Create download link
        const url = URL.createObjectURL(blob);
        const filename = `patient_${sanitizeFilename(patient.name)}_${patientId.substring(0, 8)}_${Date.now()}.json`;

        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();

        // Cleanup
        setTimeout(() => {
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }, 100);

        console.log(`✓ Export complete: ${filename} (${formatFileSize(blob.size)})`);
        showNotification(`Patient data exported: ${filename}`, 'success');

        return { success: true, filename, size: blob.size };

    } catch (error) {
        console.error('Export failed:', error);
        showNotification('Failed to export patient data', 'error');
        return { success: false, error: error.message };
    }
}

function sanitizeFilename(name) {
    return name
        .replace(/[^a-zA-Z0-9]/g, '_')
        .replace(/_+/g, '_')
        .substring(0, 30);
}

function generateSimpleChecksum(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        const char = str.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash;
    }
    return Math.abs(hash).toString(16).toUpperCase().padStart(8, '0');
}

// Expose to global scope
window.exportPatientBundle = exportPatientBundle;
